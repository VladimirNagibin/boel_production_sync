"""Провайдер Ozon Seller API.

Заготовка: структура запросов к API Ozon и маппинг заказов в общий формат.
Реальные поля ответов нужно сверить с актуальной документацией Ozon Seller.
"""

from datetime import datetime, timedelta
from typing import Any

import httpx
from fastapi import Request

from core.logger import logger
from core.settings import settings
from models.enums import MarketplaceEnum
from models.marketplace_models import MarketplaceAccount
from schemas.marketplace_schemas import (
    MarketplaceOrderCreate,
    MarketplaceOrderItemCreate,
)
from services.exceptions import MarketplaceApiError

from .base import AbstractMarketplaceProvider, MarketplaceOrdersPage

PAGE_SIZE = 100
REQUEST_TIMEOUT = 30


class OzonProvider(AbstractMarketplaceProvider):
    """Провайдер Ozon Seller API."""

    marketplace = MarketplaceEnum.OZON

    def _headers(self, account: MarketplaceAccount) -> dict[str, str]:
        """Формирует заголовки авторизации Ozon Seller API."""
        client_id = account.client_id or settings.OZON_CLIENT_ID
        api_key = account.api_key or settings.OZON_API_KEY
        if not client_id or not api_key:
            raise MarketplaceApiError(
                "Не заданы Client-Id/Api-Key для Ozon"
            )
        return {
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": "application/json",
        }

    def _api_base(self, account: MarketplaceAccount) -> str:
        """Возвращает базовый URL API Ozon."""
        return account.api_base or settings.OZON_API_BASE

    async def _post(
        self,
        account: MarketplaceAccount,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Выполняет POST-запрос к Ozon Seller API."""
        url = f"{self._api_base(account)}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT
            ) as client:
                response = await client.post(
                    url,
                    headers=self._headers(account),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise MarketplaceApiError(
                        "Некорректный формат ответа Ozon API"
                    )
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Ozon API HTTP %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise MarketplaceApiError(
                "Ошибка HTTP при запросе к Ozon API",
                status_code=exc.response.status_code,
                detail=exc.response.text,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Ozon API network error: %s", exc)
            raise MarketplaceApiError(
                "Сетевая ошибка при запросе к Ozon API"
            ) from exc

    async def list_orders(
        self,
        account: MarketplaceAccount,
        since: datetime,
        cursor: str | None = None,
    ) -> MarketplaceOrdersPage:
        """Загружает страницу заказов Ozon."""
        offset = int(cursor) if cursor and cursor.isdigit() else 0
        until = since + timedelta(
            days=settings.MARKETPLACE_ORDER_SYNC_DAYS
        )
        payload: dict[str, Any] = {
            "dir": "ASC",
            "filter": {
                "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "until": until.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "",
            },
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        data = await self._post(account, "/v3/orders/list", payload)
        result = data.get("result") or []
        total = int(data.get("total") or 0)
        orders = [self._map_order(item) for item in result]

        next_offset = offset + len(result)
        next_cursor = str(next_offset) if next_offset < total else None
        return MarketplaceOrdersPage(orders=orders, next_cursor=next_cursor)

    async def get_order(
        self,
        account: MarketplaceAccount,
        external_order_id: str,
    ) -> MarketplaceOrderCreate:
        """Возвращает один заказ Ozon по его posting_number."""
        data = await self._post(
            account,
            "/v3/orders/info",
            {"posting_number": external_order_id},
        )
        result = data.get("result") or []
        if not result:
            raise MarketplaceApiError(
                f"Заказ Ozon {external_order_id} не найден"
            )
        return self._map_order(result[0])

    async def verify_webhook(
        self,
        request: Request,
    ) -> MarketplaceOrderCreate | None:
        """Обрабатывает push-уведомление Ozon.

        TODO: реализовать проверку подписи Ozon Push и парсинг заказа.
        """
        logger.warning("Ozon webhook verification is not implemented yet")
        return None

    def _map_order(self, item: dict[str, Any]) -> MarketplaceOrderCreate:
        """Преобразует элемент ответа Ozon в общую схему заказа."""
        products = item.get("products") or []
        # TODO: уточнить единицы измерения цены (Ozon часто отдаёт копейки)
        total = sum(
            float(p.get("price") or 0) * float(p.get("quantity") or 1)
            for p in products
        )
        return MarketplaceOrderCreate(
            external_order_id=str(
                item.get("posting_number") or item.get("order_id") or ""
            ),
            status=str(item.get("status") or "unknown"),
            total=total,
            created_at=self._parse_datetime(item.get("in_process_at")),
            buyer_data=(
                item.get("buyer")
                if isinstance(item.get("buyer"), dict)
                else None
            ),
            raw_payload=item,
            items=[
                MarketplaceOrderItemCreate(
                    sku=str(p.get("sku") or ""),
                    title=p.get("name"),
                    quantity=float(p.get("quantity") or 1),
                    price=float(p.get("price") or 0),
                )
                for p in products
            ],
        )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Парсит дату из ответа Ozon."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except ValueError:
            logger.warning("Не удалось распарсить дату Ozon: %s", value)
            return None
