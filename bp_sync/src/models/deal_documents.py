from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

from .references import ShippingCompany

if TYPE_CHECKING:
    from .company_models import Company
    from .deal_models import Deal  # Типизация только при проверке типов


class Billing(Base):
    """
    Платежи
    """

    __tablename__ = "billings"
    type_bill: Mapped[str] = mapped_column(comment="Тип платежа: нал/безнал")
    amount: Mapped[float] = mapped_column(comment="Сумма платежа")
    date_payment: Mapped[date] = mapped_column(
        Date,
        comment="Дата платежа",
    )
    deal_id: Mapped[UUID] = mapped_column(ForeignKey("deals.id"))
    deal: Mapped["Deal"] = relationship("Deal", back_populates="billings")


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
