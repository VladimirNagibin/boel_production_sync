"""Схемы и перечисления для заданий на обработку счетов."""

from enum import StrEnum

from pydantic import BaseModel, Field


class InvoiceTaskAction(StrEnum):
    """Действие, которое необходимо выполнить над счётом."""

    NEW_INVOICE = "new_invoice"  # Новый счёт
    UPDATED_INVOICE = "updated_invoice"  # Обновлён счёт
    DELETED_INVOICE = "deleted_invoice"  # Удалён счёт

    @classmethod
    def get_display_name(cls, value: "InvoiceTaskAction") -> str:
        """Возвращает человекочитаемое название действия."""
        display_names = {
            cls.NEW_INVOICE: "Новый счёт",
            cls.UPDATED_INVOICE: "Обновлён счёт",
            cls.DELETED_INVOICE: "Удалён счёт",
        }
        return display_names.get(value, "Неизвестное действие")


class InvoiceTaskCreate(BaseModel):
    """Запрос на добавление задания по счёту."""

    invoice_id: int = Field(..., gt=0, description="Идентификатор счёта")
    action: InvoiceTaskAction = Field(..., description="Тип действия")


class InvoiceTaskResponse(BaseModel):
    """Ответ с информацией о задании по счёту."""

    message_id: str | None = None
    invoice_id: int
    action: InvoiceTaskAction
    status: str = "queued"
