"""Репозиторий для кабинетов, заказов и запусков синхронизации
маркетплейсов.
"""

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.enums import MarketplaceSyncStatusEnum
from models.marketplace_models import (
    MarketplaceAccount,
    MarketplaceOrder,
    MarketplaceOrderItem,
    MarketplaceSyncRun,
)
from schemas.marketplace_schemas import MarketplaceOrderCreate


class MarketplaceRepository:
    """Доступ к данным маркетплейсов."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_account(
        self, account_id: uuid.UUID
    ) -> MarketplaceAccount | None:
        """Возвращает кабинет по ID."""
        stmt = select(MarketplaceAccount).where(
            MarketplaceAccount.id == account_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_accounts(self) -> Sequence[MarketplaceAccount]:
        """Возвращает все активные кабинеты."""
        stmt = select(MarketplaceAccount).where(
            MarketplaceAccount.is_active.is_(True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_first_account_by_marketplace(
        self, marketplace: str
    ) -> MarketplaceAccount | None:
        """Возвращает первый активный кабинет маркетплейса."""
        stmt = (
            select(MarketplaceAccount)
            .where(
                MarketplaceAccount.marketplace == marketplace,
                MarketplaceAccount.is_active.is_(True),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_order_by_external_id(
        self, account_id: uuid.UUID, external_order_id: str
    ) -> MarketplaceOrder | None:
        """Возвращает заказ по внешнему ID в рамках кабинета."""
        stmt = select(MarketplaceOrder).where(
            MarketplaceOrder.account_id == account_id,
            MarketplaceOrder.external_order_id == external_order_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_order(
        self,
        account: MarketplaceAccount,
        order: MarketplaceOrderCreate,
        deal_id: int | None = None,
        sync_status: str | None = None,
        last_error: str | None = None,
    ) -> MarketplaceOrder:
        """Создаёт или обновляет заказ маркетплейса."""
        existing = await self.get_order_by_external_id(
            account.id, order.external_order_id
        )
        if existing is not None:
            existing.status = order.status
            existing.total = order.total
            existing.buyer_data = order.buyer_data
            existing.raw_payload = order.raw_payload
            if deal_id is not None:
                existing.deal_id = deal_id
                existing.synced_at = datetime.now(timezone.utc)
            if sync_status is not None:
                existing.sync_status = sync_status
            if last_error is not None:
                existing.last_error = last_error
            await self._replace_items(existing, order)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        order_db = MarketplaceOrder(
            marketplace=account.marketplace,
            account_id=account.id,
            external_order_id=order.external_order_id,
            status=order.status,
            total=order.total,
            buyer_data=order.buyer_data,
            raw_payload=order.raw_payload,
            sync_status=sync_status or MarketplaceSyncStatusEnum.NEW.value,
            deal_id=deal_id,
            last_error=last_error,
            synced_at=datetime.now(timezone.utc) if deal_id else None,
        )
        self.session.add(order_db)
        await self.session.flush()
        await self._replace_items(order_db, order)
        await self.session.commit()
        await self.session.refresh(order_db)
        return order_db

    async def _replace_items(
        self,
        order_db: MarketplaceOrder,
        order: MarketplaceOrderCreate,
    ) -> None:
        """Заменяет товарные позиции заказа."""
        order_db.items.clear()
        for item in order.items:
            order_db.items.append(
                MarketplaceOrderItem(
                    sku=item.sku,
                    title=item.title,
                    quantity=item.quantity,
                    price=item.price,
                    product_id=item.product_id,
                )
            )

    async def mark_order_synced(
        self, order_id: uuid.UUID, deal_id: int, status: str
    ) -> None:
        """Помечает заказ как синхронизированный со сделкой."""
        order = await self.session.get(MarketplaceOrder, order_id)
        if order is None:
            logger.warning("Заказ %s не найден", order_id)
            return
        order.deal_id = deal_id
        order.sync_status = status
        order.synced_at = datetime.now(timezone.utc)
        order.last_error = None
        await self.session.commit()

    async def mark_order_error(
        self, order_id: uuid.UUID, error: str
    ) -> None:
        """Помечает заказ как ошибочный."""
        order = await self.session.get(MarketplaceOrder, order_id)
        if order is None:
            logger.warning("Заказ %s не найден", order_id)
            return
        order.sync_status = MarketplaceSyncStatusEnum.ERROR.value
        order.last_error = error
        await self.session.commit()

    async def update_sync_cursor(
        self, account_id: uuid.UUID, cursor: str | None
    ) -> None:
        """Обновляет курсор синхронизации кабинета."""
        account = await self.get_account(account_id)
        if account is None:
            logger.warning("Кабинет %s не найден", account_id)
            return
        account.sync_cursor = cursor
        await self.session.commit()

    async def list_orders(
        self, account_id: uuid.UUID | None = None, limit: int = 100
    ) -> Sequence[MarketplaceOrder]:
        """Возвращает список заказов с пагинацией по лимиту."""
        stmt = (
            select(MarketplaceOrder)
            .order_by(MarketplaceOrder.created_at.desc())
            .limit(limit)
        )
        if account_id is not None:
            stmt = stmt.where(MarketplaceOrder.account_id == account_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_sync_run(
        self, account: MarketplaceAccount, status: str = "running"
    ) -> MarketplaceSyncRun:
        """Создаёт запись о запуске синхронизации."""
        run = MarketplaceSyncRun(
            marketplace=account.marketplace,
            account_id=account.id,
            status=status,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def finish_sync_run(
        self,
        run_id: uuid.UUID,
        status: str,
        orders_processed: int,
        orders_created: int,
        orders_updated: int,
        orders_with_error: int,
        error: str | None = None,
    ) -> None:
        """Завершает запись о запуске синхронизации."""
        run = await self.session.get(MarketplaceSyncRun, run_id)
        if run is None:
            logger.warning("Запуск синхронизации %s не найден", run_id)
            return
        run.status = status
        run.finished_at = datetime.now(timezone.utc)
        run.orders_processed = orders_processed
        run.orders_created = orders_created
        run.orders_updated = orders_updated
        run.orders_with_error = orders_with_error
        run.error = error
        await self.session.commit()

    async def list_sync_runs(
        self, limit: int = 100
    ) -> Sequence[MarketplaceSyncRun]:
        """Возвращает историю запусков синхронизации."""
        stmt = (
            select(MarketplaceSyncRun)
            .order_by(MarketplaceSyncRun.started_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
