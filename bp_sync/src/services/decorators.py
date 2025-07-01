from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar, cast

from fastapi import HTTPException, status

from core.logger import logger

from .exceptions import BitrixApiError, BitrixAuthError

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


def handle_bitrix_errors() -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except (BitrixAuthError, BitrixApiError):
                raise
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error while calling Bitrix24 API",
                )

        return cast(F, wrapper)

    return decorator
