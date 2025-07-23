from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Float, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

from .bases import NameStrIdEntity
from .enums import MethodPaymentEnum
from .references import ShippingCompany

if TYPE_CHECKING:
    from .company_models import Company
    from .invoice_models import Invoice


class Billing(NameStrIdEntity):
    """
    Платежи
    """

    __tablename__ = "billings"
    payment_method: Mapped[MethodPaymentEnum] = mapped_column(
        PgEnum(
            MethodPaymentEnum,
            name="payment_method_enum",
            create_type=False,
            default=MethodPaymentEnum.NOT_DEFINE,
            server_default=MethodPaymentEnum.NOT_DEFINE.value,
        ),
        comment="форма оплаты",
    )
    amount: Mapped[float] = mapped_column(Float, comment="Сумма платежа")
    date_payment: Mapped[date] = mapped_column(
        Date,
        comment="Дата платежа",
    )
    number: Mapped[str]
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.external_id"))
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", back_populates="billings"
    )


class Contract(Base):
    """
    Договора
    """

    __tablename__ = "contracts"
    shipping_company_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipping_companies.id"),
        comment="Фирма отгрузки",
    )
    shipping_company: Mapped["ShippingCompany"] = relationship(
        "ShippingCompany", back_populates="contracts"
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id"),
        comment="Фирма покупатель",
    )
    company: Mapped["Company"] = relationship(
        "Company", back_populates="contracts"
    )
    type_contract: Mapped[str] = mapped_column(
        default="С покупателем", comment="Вид договора"
    )
    number_contract: Mapped[str] = mapped_column(comment="Номер договора")
    date_contract: Mapped[date] = mapped_column(Date, comment="Дата договора")
    period_contract: Mapped[date | None] = mapped_column(
        Date, default=None, comment="Срок действия договора"
    )

    @hybrid_property  # type: ignore[misc]
    def display_info(self) -> str:
        """
        Возвращает представление договора
        Фирма: Торговый дом СР, вид договора: с покупателем,
        //Договор № 212 от 13.06.2022//, срок действия
        """
        firm_name = (
            self.shipping_company.name
            if self.shipping_company
            else "Не указана фирма"
        )
        contract_type = self.type_contract or "Не определено"
        contract_number = self.number_contract or "??"
        contract_date = (
            self.date_contract.strftime("%d.%m.%Y")
            if self.date_contract
            else "??"
        )
        period_str = (
            self.period_contract.strftime("%d.%m.%Y")
            if self.period_contract
            else ""
        )

        return (
            f"Фирма: {firm_name}, "
            f"вид договора: {contract_type}, "
            f"//Договор № {contract_number} от {contract_date}//, "
            f"срок действия {period_str}"
        )
