"""Базовые абстракции для провайдеров маркетплейсов."""

from abc import ABC, abstractmethod
from datetime import datetime

from fastapi import Request

from models.enums import MarketplaceEnum
from models.marketplace_models import MarketplaceAccount
from schemas.marketplace_schemas import MarketplaceOrderCreate


class MarketplaceOrdersPage:
    """Страница заказов и курсор для следующей выборки."""

    def __init__(
        self,
        orders: list[MarketplaceOrderCreate],
        next_cursor: str | None,
    ) -> None:
        self.orders = orders
        self.next_cursor = next_cursor


class AbstractMarketplaceProvider(ABC):
    """Базовый интерфейс провайдера маркетплейса."""

    marketplace: MarketplaceEnum

    @abstractmethod
    async def list_orders(
        self,
        account: MarketplaceAccount,
        since: datetime,
        cursor: str | None = None,
    ) -> MarketplaceOrdersPage:
        """Возвращает страницу заказов и курсор следующей страницы."""

    @abstractmethod
    async def get_order(
        self,
        account: MarketplaceAccount,
        external_order_id: str,
    ) -> MarketplaceOrderCreate:
        """Возвращает один заказ по его внешнему ID."""

    @abstractmethod
    async def verify_webhook(
        self,
        request: Request,
    ) -> MarketplaceOrderCreate | None:
        """Проверяет подпись вебхука и возвращает заказ (или None)."""
