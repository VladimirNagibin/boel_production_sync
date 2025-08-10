from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import NameStrIdEntity
from .company_models import Company as CompanyDB
from .invoice_models import Invoice as InvoiceDB
from .references import ShippingCompany, Warehouse
from .user_models import User as UserDB


class DeliveryNote(NameStrIdEntity):
    """
    Накладные из 1С
    """

    __tablename__ = "delivery_notes"

    opportunity: Mapped[float] = mapped_column(
        default=0.0, comment="Сумма сделки"
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id")
    )  # Ид компании
    company: Mapped["CompanyDB"] = relationship(
        "Company", back_populates="delivery_notes"
    )
    assigned_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID ответственного",
    )
    assigned_by: Mapped["UserDB"] = relationship(
        lambda: UserDB,
        back_populates="delivery_notes",
        foreign_keys=lambda: [DeliveryNote.assigned_by_id],
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.external_id")
    )  # Ид счёта
    invoice: Mapped["InvoiceDB"] = relationship(
        lambda: InvoiceDB,
        back_populates="delivery_notes",
        foreign_keys=lambda: [DeliveryNote.invoice_id],
    )
    shipping_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipping_companies.external_id")
    )  # Ид фирмы отгрузки
    shipping_company: Mapped["ShippingCompany"] = relationship(
        "ShippingCompany", back_populates="delivery_notes"
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.external_id")
    )  # Ид склада
    warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", back_populates="delivery_notes"
    )
    date_delivery_note: Mapped[date] = mapped_column(
        Date,
        comment="Дата накладной в 1с",
    )
