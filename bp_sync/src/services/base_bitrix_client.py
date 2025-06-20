from typing import Any

import httpx
from fastapi import status

from core.logger import logger

from .exceptions import BitrixApiError, BitrixAuthError

DEFAULT_TIMEOUT = 10


class BaseBitrixClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def _get(
        self, url: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            detail = e.response.json().get("error_description", str(e))
            logger.error(f"HTTP error: {e.response.status_code}")
            raise BitrixAuthError(
                f"HTTP error {e.response.status_code}", detail=detail
            )
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise BitrixAuthError("Network error during token request")
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise BitrixAuthError("Invalid response format from Bitrix24")

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"API HTTP error {e.response.status_code}: {e.response.text}"
            )
            raise BitrixApiError(
                status_code=e.response.status_code,
                error_description=f"Bitrix API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise BitrixApiError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error_description="Unable to connect to Bitrix24",
            )
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise BitrixApiError(
                status_code=status.HTTP_502_BAD_GATEWAY,
                error_description="Invalid response from Bitrix24",
            )
