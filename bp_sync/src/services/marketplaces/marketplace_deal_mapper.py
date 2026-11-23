"""Преобразование заказа маркетплейса в схемы сделки Битрикс24."""

from datetime import datetime, timedelta, timezone
from typing import Any

from core.settings import settings
from models.enums import MarketplaceEnum
from models.marketplace_models import MarketplaceAccount
from schemas.deal_schemas import DealCreate, DealUpdate
from schemas.marketplace_schemas import MarketplaceOrderCreate
from services.deals.enums import CreationSourceEnum, DealTypeEnum


class MarketplaceDealMapper:
    """Преобразует заказ маркетплейса в сделки Битрикс24."""

    def _base_fields(
        self,
        order: MarketplaceOrderCreate,
        account: MarketplaceAccount,
    ) -> dict[str, Any]:
        """Формирует общие поля сделки из заказа."""
        now = order.created_at or datetime.now(timezone.utc)
        closedate = now + timedelta(
            days=settings.MARKETPLACE_DEFAULT_CLOSED_DAYS
        )
        return {
            "title": (
                f"{MarketplaceEnum.get_display_name(account.marketplace)} "
                f"#{order.external_order_id}"
            ),
            "stage_id": settings.MARKETPLACE_DEFAULT_STAGE_ID,
            "category_id": 0,
            "type_id": DealTypeEnum.MARKETPLACE.value,
            "source_id": account.source_id,
            "creation_source_id": CreationSourceEnum.AUTO.value,
            "opportunity": order.total,
            "currency_id": "RUB",
            "begindate": now,
            "closedate": closedate,
            "date_create": now,
            "date_modify": now,
            "assigned_by_id": account.assigned_by_id,
            "created_by_id": account.assigned_by_id,
            "modify_by_id": account.assigned_by_id,
            "originator_id": account.marketplace,
            "origin_id": order.external_order_id,
        }

    def to_deal_create(
        self,
        order: MarketplaceOrderCreate,
        account: MarketplaceAccount,
    ) -> DealCreate:
        """Создаёт схему DealCreate для сохранения в локальную БД."""
        return DealCreate(**self._base_fields(order, account))

    def to_deal_create_for_bitrix(
        self,
        order: MarketplaceOrderCreate,
        account: MarketplaceAccount,
    ) -> DealUpdate:
        """Создаёт схему DealUpdate для вызова crm.deal.add в B24.

        DealCreate не содержит метода to_bitrix_dict, поэтому для запроса
        к Bitrix24 используется DealUpdate.
        """
        return DealUpdate(**self._base_fields(order, account))

    def to_deal_update(
        self,
        order: MarketplaceOrderCreate,
        account: MarketplaceAccount,
        deal_id: int,
    ) -> DealUpdate:
        """Создаёт схему обновления сделки из заказа."""
        return DealUpdate(
            external_id=deal_id,
            opportunity=order.total,
            originator_id=account.marketplace,
            origin_id=order.external_order_id,
        )
