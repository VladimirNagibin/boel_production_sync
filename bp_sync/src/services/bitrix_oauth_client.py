from typing import Dict
from urllib.parse import urlencode

from core.logger import logger

from .base_bitrix_client import DEFAULT_TIMEOUT, BaseBitrixClient
from .exceptions import BitrixAuthError
from .token_storage import TokenStorage

OAUTH_ENDPOINT = "/oauth/authorize/"
TOKEN_ENDPOINT = "/oauth/token/"


class BitrixOAuthClient(BaseBitrixClient):
    def __init__(
        self,
        portal_domain: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_storage: TokenStorage,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        super().__init__(timeout)
        self.portal_domain = portal_domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = f"{portal_domain}{TOKEN_ENDPOINT}"
        self.token_storage = token_storage

    async def get_valid_token(self) -> str:
        if access_token := await self.token_storage.get_token("access_token"):
            return access_token
        if refresh_token := await self.token_storage.get_token(
            "refresh_token"
        ):
            return await self._refresh_access_token(refresh_token)
        logger.warning(
            "No valid tokens available, re-authentication required."
        )
        raise BitrixAuthError(
            "Authentication required",
            detail=f"Re-authorize at: {self.get_auth_url()}",
        )

    async def _refresh_access_token(self, refresh_token: str) -> str:
        """Обновление токена доступа"""
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        token_data = await self._get(self.token_url, params=params)
        if "error" in token_data:
            error_msg = token_data.get(
                "error_description", "Unknown OAuth error"
            )
            logger.error(f"Bitrix OAuth error: {error_msg}")
            raise BitrixAuthError(detail=f"OAuth error: {error_msg}")
        access_token = token_data["access_token"]
        if not isinstance(access_token, str):
            logger.error(
                f"Invalid access_token type: {type(access_token).__name__}"
            )
            raise BitrixAuthError(detail="Invalid access_token format")

        await self._save_tokens(token_data)
        logger.info("Access token refreshed successfully")
        return access_token

    async def fetch_token(self, code: str) -> str:
        """Получение токена по коду авторизации"""
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        token_data = await self._get(self.token_url, params=params)
        if "error" in token_data:
            error_msg = token_data.get(
                "error_description", "Unknown OAuth error"
            )
            logger.error(f"Bitrix OAuth error: {error_msg}")
            raise BitrixAuthError(detail=f"OAuth error: {error_msg}")
        access_token = token_data["access_token"]
        if not isinstance(access_token, str):
            logger.error(
                f"Invalid access_token type: {type(access_token).__name__}"
            )
            raise BitrixAuthError(detail="Invalid access_token format")
        await self._save_tokens(token_data)
        logger.info("New tokens fetched and saved successfully")
        return access_token

    async def _save_tokens(self, token_data: Dict[str, str]) -> None:
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
