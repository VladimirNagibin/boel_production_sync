"""Модели для хранения кабинетов, заказов и запусков синхронизации
маркетплейсов.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base
from models.enums import MarketplaceSyncStatusEnum


class MarketplaceAccount(Base):
    """Кабинет продавца в маркетплейсе."""

    __tablename__ = "marketplace_accounts"

    marketplace: Mapped[str] = mapped_column(
        String(32), comment="Код маркетплейса"
    )
    name: Mapped[str] = mapped_column(String(255), comment="Название кабинета")
    client_id: Mapped[str | None] = mapped_column(
        String(255), comment="Client ID кабинета"
    )
    # TODO: хранить ключ в зашифрованном виде (TokenCipher / Redis)
    api_key: Mapped[str | None] = mapped_column(
        String(512), comment="API-ключ кабинета"
    )
    api_base: Mapped[str | None] = mapped_column(
        String(255), comment="Базовый URL API маркетплейса"
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.external_id"), comment="Источник сделки"
    )
    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"), comment="Ответственный по умолчанию"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Кабинет активен"
    )
    sync_cursor: Mapped[str | None] = mapped_column(
        String(255), comment="Курсор последней синхронизации"
    )

    orders: Mapped[list["MarketplaceOrder"]] = relationship(
        "MarketplaceOrder", back_populates="account"
    )


class MarketplaceOrder(Base):
    """Заказ, выгруженный из маркетплейса."""

    __tablename__ = "marketplace_orders"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "external_order_id",
            name="uq_marketplace_order_account_external",
        ),
    )

    marketplace: Mapped[str] = mapped_column(String(32))
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("marketplace_accounts.id"), index=True
    )
    external_order_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64))
    total: Mapped[float] = mapped_column(default=0.0)
    buyer_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict
    )
    sync_status: Mapped[str] = mapped_column(
        String(32), default=MarketplaceSyncStatusEnum.NEW.value
    )
    deal_id: Mapped[int | None] = mapped_column(
        ForeignKey("deals.external_id"), index=True
    )
    last_error: Mapped[str | None] = mapped_column(String(1024))
    synced_at: Mapped[datetime | None] = mapped_column()

    account: Mapped["MarketplaceAccount"] = relationship(
        "MarketplaceAccount", back_populates="orders"
    )
    items: Mapped[list["MarketplaceOrderItem"]] = relationship(
        "MarketplaceOrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MarketplaceOrderItem(Base):
    """Товарная позиция заказа маркетплейса."""

    __tablename__ = "marketplace_order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("marketplace_orders.id"), index=True
    )
    sku: Mapped[str] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(512))
    quantity: Mapped[float] = mapped_column(default=1.0)
    price: Mapped[float] = mapped_column(default=0.0)
    product_id: Mapped[int | None] = mapped_column()

    order: Mapped["MarketplaceOrder"] = relationship(
        "MarketplaceOrder", back_populates="items"
    )


class MarketplaceSyncRun(Base):
    """Запуск синхронизации заказов маркетплейса."""

    __tablename__ = "marketplace_sync_runs"

    marketplace: Mapped[str | None] = mapped_column(String(32))
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("marketplace_accounts.id")
    )
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[datetime] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    orders_processed: Mapped[int] = mapped_column(default=0)
    orders_created: Mapped[int] = mapped_column(default=0)
    orders_updated: Mapped[int] = mapped_column(default=0)
    orders_with_error: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(String(2048))
