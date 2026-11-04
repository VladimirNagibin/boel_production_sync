"""Модели для таблицы правил согласования цен (price_permisson)."""

from decimal import Decimal

from sqlalchemy import BigInteger, Index, Numeric, true
from sqlalchemy.orm import Mapped, mapped_column

from db.postgres import Base


class PricePermission(Base):
    """Правило согласования цены.

    Таблица-справочник разрешённых цен и сроков оплаты для комбинации
    «компания — товар — фирма — тип оплаты». Используется при проверке
    возможности продажи по запрошенной цене.
    """

    __tablename__ = "price_permisson"
    __table_args__ = (
        Index(
            "ix_price_permisson_lookup",
            "id_company",
            "id_product",
            "id_firm",
            "payment_type",
        ),
    )

    id_company: Mapped[int] = mapped_column(
        comment="ID компании (внешний код в Битрикс24)"
    )
    id_product: Mapped[int] = mapped_column(
        comment="ID товара"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), comment="Цена"
    )
    id_deal: Mapped[int] = mapped_column(
        comment="ID сделки (внешний код в Битрикс24)"
    )
    id_firm: Mapped[int] = mapped_column(
        comment="ID фирмы отгрузки"
    )
    payment_type: Mapped[int] = mapped_column(
        comment=(
            "Тип оплаты: 493 — предоплата, "
            "495 — отсрочка, 497 — частичная"
        )
    )
    payment_term: Mapped[int] = mapped_column(
        comment="Срок оплаты (дней)"
    )

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return (
            f"<PricePermission(id_company={self.id_company}, "
            f"id_product={self.id_product}, price={self.price})>"
        )


class InvoiceBusy(Base):
    """Блокировка счёта на время обработки.

    Используется для предотвращения параллельной обработки одного и того же
    счёта вебхуком. Запись с ``busy = true`` означает, что счёт в данный
    момент занят.
    """

    __tablename__ = "invoice_busy"

    id_invoice: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        comment="ID счёта (внешний код в Битрикс24)",
    )
    busy: Mapped[bool] = mapped_column(
        default=True,
        server_default=true(),
        comment="Признак занятости счёта",
    )

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return f"<InvoiceBusy(id_invoice={self.id_invoice}, busy={self.busy})>"
