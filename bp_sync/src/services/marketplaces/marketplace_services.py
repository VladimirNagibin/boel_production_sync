"""Оркестрация загрузки заказов маркетплейсов и синхронизации сделок."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request

from core.logger import logger
from core.settings import settings
from models.enums import MarketplaceEnum, MarketplaceSyncStatusEnum
from models.marketplace_models import MarketplaceAccount
from schemas.marketplace_schemas import MarketplaceOrderCreate
from services.deals.deal_services import DealClient
from services.exceptions import ConflictException, MarketplaceSyncError

from .marketplace_deal_mapper import MarketplaceDealMapper
from .marketplace_repository import MarketplaceRepository
from .providers import get_provider


class MarketplaceService:
    """Сервис синхронизации заказов маркетплейса со сделками."""

    def __init__(
        self,
        repository: MarketplaceRepository,
        deal_client: DealClient,
    ) -> None:
        self.repository = repository
        self.deal_client = deal_client
        self.mapper = MarketplaceDealMapper()

    async def sync_accounts(
        self, since: datetime | None = None
    ) -> dict[str, Any]:
        """Запускает синхронизацию по всем активным кабинетам."""
        accounts = await self.repository.get_active_accounts()
        results: list[dict[str, Any]] = []
        for account in accounts:
            results.append(await self.sync_account(account, since))
        return {"accounts": results}

    async def sync_account(
        self,
        account: MarketplaceAccount,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Синхронизирует заказы одного кабинета."""
        provider = get_provider(MarketplaceEnum(account.marketplace))
        since = since or (
            datetime.now(timezone.utc)
            - timedelta(days=settings.MARKETPLACE_ORDER_SYNC_DAYS)
        )
        run = await self.repository.create_sync_run(account)

        created = 0
        updated = 0
        errors = 0

        try:
            page = await provider.list_orders(
                account, since, account.sync_cursor
            )
            for order in page.orders:
                try:
                    result = await self.process_order(account, order)
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
                except Exception as exc:
                    errors += 1
                    logger.exception(
                        "Ошибка обработки заказа %s: %s",
                        order.external_order_id,
                        exc,
                    )

            if page.next_cursor:
                await self.repository.update_sync_cursor(
                    account.id, page.next_cursor
                )

            await self.repository.finish_sync_run(
                run.id,
                status="success",
                orders_processed=created + updated + errors,
                orders_created=created,
                orders_updated=updated,
                orders_with_error=errors,
            )
        except Exception as exc:
            await self.repository.finish_sync_run(
                run.id,
                status="error",
                orders_processed=created + updated + errors,
                orders_created=created,
                orders_updated=updated,
                orders_with_error=errors,
                error=str(exc),
            )
            raise

        return {
            "account_id": str(account.id),
            "marketplace": account.marketplace,
            "created": created,
            "updated": updated,
            "errors": errors,
        }

    async def process_order(
        self,
        account: MarketplaceAccount,
        order: MarketplaceOrderCreate,
    ) -> str:
        """Создаёт или обновляет сделку по заказу маркетплейса."""
        existing = await self.repository.get_order_by_external_id(
            account.id, order.external_order_id
        )
        deal_id = existing.deal_id if existing is not None else None

        if deal_id is None:
            deal_id = await self._find_existing_deal(account, order)

        if deal_id is not None:
            return await self._update_deal(account, order, deal_id)

        return await self._create_deal(account, order)

    async def _create_deal(
        self,
        account: MarketplaceAccount,
        order: MarketplaceOrderCreate,
    ) -> str:
        """Создаёт сделку в Битрикс24 и локальную запись заказа."""
        deal_create = self.mapper.to_deal_create(order, account)
        deal_for_bitrix = self.mapper.to_deal_create_for_bitrix(
            order, account
        )
        deal_id = await self.deal_client.bitrix_client.create(
            deal_for_bitrix
        )
        if not deal_id:
            raise MarketplaceSyncError(
                f"Не удалось создать сделку для заказа "
                f"{order.external_order_id}"
            )

        deal_create.external_id = deal_id
        try:
            await self.deal_client.repo.create_entity(deal_create)
        except ConflictException:
            logger.warning(
                "Сделка %s уже существует в БД — продолжаем", deal_id
            )

        await self.repository.upsert_order(
            account,
            order,
            deal_id=deal_id,
            sync_status=MarketplaceSyncStatusEnum.DEAL_CREATED.value,
        )
        return "created"

    async def _update_deal(
        self,
        account: MarketplaceAccount,
        order: MarketplaceOrderCreate,
        deal_id: int,
    ) -> str:
        """Обновляет сделку в Битрикс24 и локальную запись заказа."""
        deal_db = await self.deal_client.repo.get(deal_id)
        if deal_db is None:
            await self.deal_client.import_from_bitrix(deal_id)

        deal_update = self.mapper.to_deal_update(order, account, deal_id)
        await self.deal_client.bitrix_client.update(deal_update)
        await self.deal_client.repo.update_entity(deal_update)

        await self.repository.upsert_order(
            account,
            order,
            deal_id=deal_id,
            sync_status=MarketplaceSyncStatusEnum.DEAL_UPDATED.value,
        )
        return "updated"

    async def _find_existing_deal(
        self,
        account: MarketplaceAccount,
        order: MarketplaceOrderCreate,
    ) -> int | None:
        """Ищет сделку по маркеру происхождения (originator_id/origin_id)."""
        result = await self.deal_client.bitrix_client.list(
            select=["ID"],
            filter_entity={
                "ORIGINATOR_ID": account.marketplace,
                "ORIGIN_ID": order.external_order_id,
            },
        )
        if result and result.result:
            external_id = result.result[0].external_id
            return int(external_id) if external_id is not None else None
        return None

    async def handle_webhook(
        self,
        marketplace: MarketplaceEnum,
        request: Request,
    ) -> str:
        """Обрабатывает вебхук маркетплейса."""
        provider = get_provider(marketplace)
        order = await provider.verify_webhook(request)
        if order is None:
            return "ignored"

        account = await self.repository.get_first_account_by_marketplace(
            marketplace.value
        )
        if account is None:
            raise MarketplaceSyncError(
                f"Нет активного кабинета для {marketplace.value}"
            )
        return await self.process_order(account, order)
