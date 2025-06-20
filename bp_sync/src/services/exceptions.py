from typing import Any

from fastapi import HTTPException


class BitrixAuthError(Exception):
    def __init__(
        self,
        message: str = "Bitrix authentication failed",
        detail: dict[Any, Any] | str | None = None,
    ):
        self.message = message
        self.detail = detail
        super().__init__(message)


class BitrixApiError(HTTPException):
    def __init__(
        self,
        status_code: int = 500,
        error_description: str = "Unknown Bitrix API error",
    ):
        super().__init__(
            status_code=status_code,
            detail=f"Bitrix API error: {error_description}",
        )
