"""Схемы для интеграции с маркетплейсами."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MarketplaceOrderItemCreate(BaseModel):
    """Товарная позиция заказа маркетплейса."""

    sku: str
    title: str | None = None
    quantity: float = 1.0
    price: float = 0.0
    product_id: int | None = None


class MarketplaceOrderCreate(BaseModel):
    """Заказ, полученный из API маркетплейса."""

    external_order_id: str
    status: str
    total: float = 0.0
    created_at: datetime | None = None
    buyer_data: dict[str, Any] | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    items: list[MarketplaceOrderItemCreate] = Field(default_factory=list)


class MarketplaceSyncRequest(BaseModel):
    """Запрос на запуск синхронизации заказов."""

    account_id: uuid.UUID | None = None
    since: datetime | None = None


class MarketplaceAccountRead(BaseModel):
    """Кабинет маркетплейса (ответ API)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    marketplace: str
    name: str
    is_active: bool
    source_id: str | None
    assigned_by_id: int
