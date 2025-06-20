from typing import Any, cast
from urllib.parse import urljoin

from fastapi import status

from core.logger import logger

from .base_bitrix_client import DEFAULT_TIMEOUT, BaseBitrixClient
from .bitrix_oauth_client import BitrixOAuthClient
from .exceptions import BitrixApiError, BitrixAuthError

MAX_RETRIES = 2
REST_API_BASE = "/rest/"
TOKEN_ERRORS = {"expired_token", "invalid_token"}


class BitrixAPIClient(BaseBitrixClient):
    def __init__(
        self,
        oauth_client: BitrixOAuthClient,
        api_base_url: str = "",
        max_retries: int = MAX_RETRIES,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        super().__init__(timeout)
        self.oauth_client = oauth_client
        self.api_base_url = (
            api_base_url or f"{oauth_client.portal_domain}{REST_API_BASE}"
        )
        self.max_retries = max_retries

    async def call_api(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Отправка API запроса к Bitrix24

        Args:
            method: API метод (например 'crm.deal.list')
            params: Параметры запроса
        """
        attempt = 0
        while attempt <= self.max_retries:
            attempt += 1
            try:
                access_token = await self.oauth_client.get_valid_token()
                url = urljoin(self.api_base_url, method)
                payload = {"auth": access_token}
                if params:
                    payload.update(params)
                response = await self._post(url, payload)
                if "error" in response:
                    self._handle_api_error(response, attempt)
                result = response.get("result", response)

                # Гарантируем, что возвращаем словарь
                if isinstance(result, dict):
                    return cast(dict[str, Any], result)
                logger.warning(
                    "API response result is not a dictionary: "
                    f"{type(result).__name__}"
                )
                # Оборачиваем не-dict результат в словарь
                return {"result": result}

                # return result.get("result", result)
            except BitrixAuthError as e:
                logger.error(f"Authentication error: {str(e)}")
                if attempt > self.max_retries:
                    raise
                continue
        raise BitrixAuthError("Token refresh failed after retries")

    def _handle_api_error(
        self, response: dict[str, Any], attempt: int
    ) -> None:
        """Обработка ошибок в ответе API"""
        error_code = response.get("error", "unknown_error")
        error_desc = response.get(
            "error_description", "Unknown Bitrix API error"
        )
        if error_code in TOKEN_ERRORS and attempt <= self.max_retries:
            logger.warning(
                "Token error detected, retrying "
                f"(attempt {attempt}/{self.max_retries})"
            )
            self._invalidate_current_token()
            raise BitrixAuthError("Token invalid or expired")
        logger.error(f"Bitrix API error [{error_code}]: {error_desc}")
        raise BitrixApiError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_description=f"Bitrix API error: {error_desc} ({error_code})",
        )

    def _invalidate_current_token(self) -> None:
        """Инвалидация текущего access token"""
        try:
            # В фоновом режиме удаляем токен, не блокируя основной поток
            import asyncio

            asyncio.create_task(
                self.oauth_client.token_storage.delete_token("access_token")
            )
        except Exception as e:
            logger.warning(f"Failed to invalidate token: {e}")
