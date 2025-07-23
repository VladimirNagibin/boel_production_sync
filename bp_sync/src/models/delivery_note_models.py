from sqlalchemy import ForeignKey
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
    # billings: Mapped[list["Billing"]] = relationship(
    #    "Billing", back_populates="delivery_note"
    # )

    @property
    def total_paid(self) -> float:
        """Общая сумма оплаченных платежей"""
        return (
            sum(billing.amount for billing in self.billings)
            if self.billings
            else 0.0
        )

    @property
    def paid_status(self) -> str:
        """Статус оплаты:
        - 'paid' - полностью оплачена
        - 'partial' - частично оплачена
        - 'unpaid' - не оплачена
        """
        total_paid = self.total_paid

        if abs(total_paid - self.opportunity) < 0.01:
            return "paid"
        elif total_paid > 0:
            return "partial"
        else:
            return "unpaid"

    @property
    def paid_percentage(self) -> float:
        """Процент оплаты от общей суммы"""
        if self.opportunity > 0:
            return float(
                min(
                    100.0, round((self.total_paid / self.opportunity) * 100, 2)
                )
            )
        return 0.0

    @property
    def payment_diff(self) -> float:
        """Оставшаяся сумма к оплате"""
        return float(max(0.0, self.opportunity - self.total_paid))
