from typing import Any

from fastapi import HTTPException, status


class BitrixAuthError(Exception):
    def __init__(
        self,
        message: str = "Bitrix authentication failed",
        detail: dict[Any, Any] | str | None = None,
    ):
        self.message = message
        self.detail = detail
        super().__init__(message)


class BitrixApiError(HTTPException):  # type: ignore[misc]
    """Custom exception for Bitrix24 API errors"""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error: str = "Unknown error",
        error_description: str = "Unknown Bitrix API error",
    ):
        super().__init__(
            status_code=status_code,
            detail={"error": error, "error_description": error_description},
        )
        self.detail: dict[str, str] = {
            "error": error,
            "error_description": error_description,
        }

    def is_bitrix_error(self, expected_error: str) -> bool:
        """Проверяет, является ли ошибка заданного типа"""
        return bool(self.detail.get("error_description") == expected_error)

    def is_not_found_error(self) -> bool:
        """Проверяет, является ли ошибка ошибкой 'Not Found'"""
        return (
            self.status_code == status.HTTP_400_BAD_REQUEST
            and self.is_bitrix_error("Not found")
        )


class ConflictException(HTTPException):  # type: ignore[misc]
    def __init__(self, entity: str, external_id: str | int):
        detail = f"{entity} with ID: {external_id} already exists"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class CyclicCallException(Exception):
    pass


class DealProcessingError(Exception):
    """Исключение для ошибок обработки сделки"""

    pass


class WebhookValidationError(Exception):
    """Кастомное исключение для ошибок валидации вебхуков"""

    pass


class WebhookSecurityError(Exception):
    """Кастомное исключение для ошибок безопасности вебхуков"""

    pass


class LockAcquisitionError(Exception):
    """Ошибка получения блокировки"""

    pass


class MaxRetriesExceededError(LockAcquisitionError):
    """Достигнуто максимальное количество попыток"""

    pass
