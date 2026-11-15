"""Сервис нумерации документов (счета и договора)."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.numbering import DocumentType, NumberingRule


@dataclass(frozen=True, slots=True)
class DocumentNumber:
    """Результат выдачи очередного номера документа."""

    number: str
    rule_id: UUID
    prefix: str
    length: int
    current_number: int


class NumberingService:
    """Сервис работы со счётчиками нумерации документов."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _coerce_doc_type(doc_type: DocumentType | str) -> DocumentType:
        """Приводит тип документа к значению перечисления."""
        if isinstance(doc_type, DocumentType):
            return doc_type
        try:
            return DocumentType(doc_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown document type: {doc_type}",
            ) from e

    @staticmethod
    def format_number(prefix: str, current_number: int, length: int) -> str:
        """Формирует номер по шаблону ``{prefix}{current:0{length}d}``."""
        if length < 1:
            raise ValueError("Длина номера должна быть больше нуля")
        return f"{prefix}{current_number:0{length}d}"

    async def get_current_number(
        self, id_firm: int, doc_type: DocumentType | str
    ) -> int | None:
        """Возвращает текущий номер счётчика без его увеличения."""
        doc_type_enum = self._coerce_doc_type(doc_type)
        try:
            stmt = select(NumberingRule.current_number).where(
                NumberingRule.id_firm == id_firm,
                NumberingRule.doc_type == doc_type_enum,
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching numbering rule for "
                f"id_firm={id_firm}, doc_type={doc_type_enum.value}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def get_next_number(
        self, id_firm: int, doc_type: DocumentType | str
    ) -> DocumentNumber:
        """Атомарно увеличивает счётчик и возвращает очередной номер.

        Операция выполняется одним запросом ``UPDATE ... RETURNING``,
        что гарантирует корректность нумерации при конкурентных вызовах.
        """
        doc_type_enum = self._coerce_doc_type(doc_type)
        try:
            stmt = (
                update(NumberingRule)
                .where(
                    NumberingRule.id_firm == id_firm,
                    NumberingRule.doc_type == doc_type_enum,
                )
                .values(
                    current_number=NumberingRule.current_number + 1,
                )
                .returning(
                    NumberingRule.id,
                    NumberingRule.prefix,
                    NumberingRule.length,
                    NumberingRule.current_number,
                )
            )
            result = await self.session.execute(stmt)
            row = result.one_or_none()

            if row is None:
                await self.session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"NumberingRule not found for id_firm={id_firm}, "
                        f"doc_type={doc_type_enum.value}"
                    ),
                )

            rule_id, prefix, length, current_number = row
            number = self.format_number(prefix, current_number, length)
            await self.session.commit()
            logger.info(
                f"Number generated for id_firm={id_firm}, "
                f"doc_type={doc_type_enum.value}: {number}"
            )
            return DocumentNumber(
                number=number,
                rule_id=rule_id,
                prefix=prefix,
                length=length,
                current_number=current_number,
            )
        except ValueError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid numbering rule: {e}",
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error generating number for id_firm={id_firm}, "
                f"doc_type={doc_type_enum.value}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e
