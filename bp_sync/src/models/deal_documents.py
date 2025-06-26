from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

if TYPE_CHECKING:
    from .deal import Deal  # Типизация только при проверке типов


class Billing(Base):
    """
    Платежи
    """

    __tablename__ = "billings"
    type_bill: Mapped[str] = mapped_column(comment="Тип платежа: нал/безнал")
    amount: Mapped[float] = mapped_column(comment="Сумма платежа")
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment="Дата платежа",
    )
    deal_id: Mapped[UUID] = mapped_column(ForeignKey("deals.id"))
    deal: Mapped["Deal"] = relationship("Deal", back_populates="billings")
