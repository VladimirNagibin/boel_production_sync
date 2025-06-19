import httpx
from functools import lru_cache
from typing import Any
from urllib.parse import urlencode

from fastapi import Depends, HTTPException, status

from core.logger import logger
from core.settings import settings
from .exceptions import BitrixApiError, BitrixAuthError
from .token_storage import get_token_storage, TokenStorage

OAUTH_ENDPOINT = "/oauth/authorize/"
TOKEN_ENDPOINT = "/oauth/token/"
REST_API_BASE = "/rest/"
TIMEOUT = 10
TOKEN_ERRORS = {"expired_token", "invalid_token"}


class Bitrix24TokenManager:
    def __init__(self, token_storage: TokenStorage):
        self.client_id = settings.BITRIX_CLIENT_ID
        self.client_secret = settings.BITRIX_CLIENT_SECRET
        self.redirect_uri = settings.BITRIX_REDIRECT_URI
        self.portal_domain = settings.BITRIX_PORTAL
        self.token_url = f"{self.portal_domain }{TOKEN_ENDPOINT}"
        self.token_storage = token_storage

    async def get_valid_token(self) -> str:
        """Получение валидного токена с автоматическим обновлением"""
        if access_token := await self.token_storage.get_token(
            token_type="access_token"
        ):
            return access_token
        if refresh_token := await self.token_storage.get_token(
            token_type="refresh_token"
        ):
            return await self._refresh_access_token(refresh_token)
        logger.warning(
            "No valid tokens available, requiring re-authentication"
        )
        raise BitrixAuthError(
            "Authentication required",
            detail=(
                "Authentication required. Please authorize via: "
                f"{self.get_auth_url()}"
            )
        )

    async def _refresh_access_token(self, refresh_token: str) -> str:
        """Обновление токена доступа"""
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        try:
            token_data = await self._request_token(params)
        except BitrixAuthError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise
        if "error" in token_data:
            error_msg = token_data.get(
                "error_description", "Unknown OAuth error"
            )
            logger.error(f"Bitrix OAuth error: {error_msg}")
            raise BitrixAuthError(detail=f"OAuth error: {error_msg}")
        await self._save_tokens(token_data)
        logger.info("Access token refreshed successfully")
        return token_data["access_token"]

    async def fetch_token(self, code: str) -> str | None:
        """Получение токена по коду авторизации"""
        params: dict[str, str] = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        try:
            token_data = await self._request_token(params)
        except BitrixAuthError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise
        if "error" in token_data:
            error_msg = token_data.get(
                "error_description", "Unknown OAuth error"
            )
            logger.error(f"Bitrix OAuth error: {error_msg}")
            raise BitrixAuthError(detail=f"OAuth error: {error_msg}")
        await self._save_tokens(token_data)
        logger.info("New tokens fetched and saved successfully")
        return token_data["access_token"]

    async def _request_token(self, params: dict[str, Any]) -> dict[str, Any]:
        """Выполнение запроса для получения токенов"""
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.get(self.token_url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("error_description", str(e))
            logger.error(
                f"Refresh token failed: HTTP {e.response.status_code}"
            )
            raise BitrixAuthError(
                f"HTTP error: {e.response.status_code}", detail=error_detail
            )
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise BitrixAuthError("Network error during token request")
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise BitrixAuthError("Invalid response format from Bitrix24")

    async def _save_tokens(self, token_data: dict[str, str]):
        """Сохранение полученных токенов"""
        try:
            await self.token_storage.save_token(
                token_data["access_token"],
                "access_token",
                expire_seconds=int(token_data["expires_in"]),
            )
            await self.token_storage.save_token(
                token_data["refresh_token"],
                "refresh_token",
            )
            logger.debug("Tokens saved to storage")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            raise RuntimeError("Token storage failure") from e

    def get_auth_url(self) -> str:
        """Генерация URL для авторизации в Bitrix24"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }

        return f"{self.portal_domain}{OAUTH_ENDPOINT}?{urlencode(params)}"


class BitrixAPIClient:
    def __init__(self, token_manager: Bitrix24TokenManager):
        self.api_url = f"{settings.BITRIX_PORTAL}{REST_API_BASE}"
        self.token_manager = token_manager

    async def call_api(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """
        Отправка API запроса к Bitrix24

        Args:
            method: API метод (например 'crm.deal.list')
            params: Параметры запроса
            max_retries: Максимальное количество попыток при ошибке токена
        """
        attempt = 0
        while attempt <= max_retries:
            attempt += 1

            try:
                access_token = await self.token_manager.get_valid_token()
                response = await self._execute_api_request(
                    method, access_token, params
                )
                # Обработка ошибок в ответе API
                if "error" in response:
                    self._handle_api_error(
                        response, attempt, max_retries
                    )
                return response.get("result", response)

            except BitrixAuthError as e:
                logger.error(f"Authentication error: {str(e)}")
                if attempt > max_retries:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=str(e)
                    )
                continue
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed after retry"
        )

    async def _execute_api_request(
        self,
        method: str,
        access_token: str,
        params: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Выполнение HTTP запроса к API"""
        url = f"{self.api_url}{method}"
        payload: dict[str, Any] = {"auth": access_token, **(params or {})}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"API HTTP error {e.response.status_code}: {e.response.text}"
            )
            raise BitrixApiError(
                status_code=e.response.status_code,
                error_description=f"Bitrix API error: {e.response.text}"
            )
        except httpx.RequestError as e:
            logger.error(f"Network error: {e}")
            raise BitrixApiError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error_description="Unable to connect to Bitrix24"
            )
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise BitrixApiError(
                status_code=status.HTTP_502_BAD_GATEWAY,
                error_description="Invalid response from Bitrix24"
            )

    def _handle_api_error(
        self,
        response: dict[str, Any],
        attempt: int,
        max_retries: int
    ) -> None:
        """Обработка ошибок в ответе API"""
        error_code = response.get("error", "unknown_error")
        error_msg = response.get(
            "error_description", "Unknown Bitrix API error"
        )

        if error_code in TOKEN_ERRORS and attempt <= max_retries:
            logger.warning(
                "Token error detected, retrying "
                f"(attempt {attempt}/{max_retries})"
            )
            self._invalidate_current_token()
            raise BitrixAuthError("Token invalid or expired")

        logger.error(f"Bitrix API error [{error_code}]: {error_msg}")
        raise BitrixApiError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_description=f"Bitrix API error: {error_msg} ({error_code})"
        )

    def _invalidate_current_token(self) -> None:
        """Инвалидация текущего access token"""
        try:
            # В фоновом режиме удаляем токен, не блокируя основной поток
            import asyncio
            asyncio.create_task(
                self.token_manager.token_storage.delete_token("access_token")
            )
        except Exception as e:
            logger.warning(f"Failed to invalidate token: {e}")

    # Примеры конкретных методов API
    async def get_deal(self, deal_id: int) -> dict[Any, Any]:
        """Получение сделки по ID"""
        return await self.call_api("crm.deal.get", {"id": deal_id})

    async def create_deal(self, deal_data: dict) -> dict:
        """Создание новой сделки"""
        return await self.call_api("crm.deal.add", {"fields": deal_data})

    async def update_deal(self, deal_id: int, deal_data: dict) -> dict:
        """Обновление сделки"""
        return await self.call_api("crm.deal.update", {"id": deal_id, "fields": deal_data})

    async def list_deals(self, filter_params: dict = None, select: list = None) -> list:
        """Список сделок с фильтрацией"""
        params = {}
        if filter_params:
            params["filter"] = filter_params
        if select:
            params["select"] = select

        return await self.call_api("crm.deal.list", params)


@lru_cache()
def get_token_manager(
    token_storage: TokenStorage = Depends(get_token_storage),
) -> Bitrix24TokenManager:
    return Bitrix24TokenManager(token_storage)


@lru_cache()
def get_bitrix_client(
    token_manager: Bitrix24TokenManager = Depends(get_token_manager),
) -> BitrixAPIClient:
    return BitrixAPIClient(token_manager)
