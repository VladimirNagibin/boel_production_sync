"""Модель правил нумерации документов (счета и договора)."""

from enum import StrEnum

from sqlalchemy import BigInteger, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column

from db.postgres import Base


class DocumentType(StrEnum):
    """Тип документа, для которого ведётся сквозная нумерация."""

    INVOICE = "invoice"  # Счёт
    CONTRACT = "contract"  # Договор


class NumberingRule(Base):
    """Правило нумерации документов.

    Для пары «фирма отгрузки — тип документа» хранится ровно один счётчик
    (``current_number``), префикс и формат итогового номера.
    """

    __tablename__ = "numbering_rules"
    __table_args__ = (
        UniqueConstraint(
            "id_firm",
            "doc_type",
            name="uq_numbering_rules_firm_doc_type",
        ),
    )

    id_firm: Mapped[int] = mapped_column(
        comment="ID фирмы отгрузки (shipping_companies.external_id)"
    )
    doc_type: Mapped[DocumentType] = mapped_column(
        PgEnum(
            DocumentType,
            name="doc_type_enum",
            values_callable=lambda enum: [member.value for member in enum],
            create_type=False,
        ),
        nullable=False,
        comment="Тип документа",
    )
    prefix: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        comment="Префикс номера документа",
    )
    length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=6,
        server_default=text("6"),
        comment="Длина номера после дополнения нулями (6 → 000001)",
    )
    current_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Последний выданный номер (без префикса)",
    )

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return (
            f"<NumberingRule(id_firm={self.id_firm}, "
            f"doc_type={self.doc_type.value}, prefix={self.prefix!r}, "
            f"current_number={self.current_number})>"
        )
