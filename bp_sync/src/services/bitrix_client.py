import httpx
from functools import lru_cache
from typing import Any
from urllib.parse import urlencode

from fastapi import Depends, HTTPException

from core.settings import settings
from .token_storage import get_token_storage, TokenStorage


class Bitrix24Client:
    def __init__(self, token_storage: TokenStorage):
        self.client_id = settings.BITRIX_CLIENT_ID
        self.client_secret = settings.BITRIX_CLIENT_SECRET
        self.redirect_uri = settings.BITRIX_REDIRECT_URI
        self.bitrix_domain = settings.BITRIX_PORTAL
        self.token_url = f"{self.bitrix_domain}/oauth/token/"
        self.api_url = f"{self.bitrix_domain}/rest/"
        self.token_storage = token_storage

    async def get_valid_token(self) -> str | None:
        """Получение валидного токена с автоматическим обновлением"""
        if access_token := await self.token_storage.get_token(
            token_type="access_token"
        ):
            return access_token
        if refresh_token := await self.token_storage.get_token(
            token_type="refresh_token"
        ):
            if access_token := await self._refresh_access_token(refresh_token):
                return access_token

    async def _refresh_access_token(self, refresh_token: str) -> str | None:
        """Обновление токена доступа"""

        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.token_url, params=params)
            token_data = response.json()

        if "error" in token_data:
            return None

        await self._save_tokens(token_data)
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

        async with httpx.AsyncClient() as client:
            response = await client.get(self.token_url, params=params)
            token_data = response.json()

        if "error" in token_data:
            return None

        await self._save_tokens(token_data)
        return token_data["access_token"]

    async def _save_tokens(self, token_data: dict[str, str]):
        """Сохранение полученных токенов"""
        await self.token_storage.save_token(
            token_data["access_token"],
            "access_token",
            expires_in=int(token_data["expires_in"]),
        )
        await self.token_storage.save_token(
            token_data["refresh_token"],
            "refresh_token",
        )

    def _get_auth_url(self) -> str:
        """Генерация URL для авторизации в Bitrix24"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }

        return f"{self.bitrix_domain}/oauth/authorize/?{urlencode(params)}"

    async def call_api(
        self,
        method: str,
        params: dict[Any, Any] | None = None,
    ) -> dict[Any, Any]:
        """
        Отправка API запроса к Bitrix24

        :param method: API метод (например 'crm.deal.list')
        :param params: Параметры запроса
        """
        access_token = await self.get_valid_token()
        if not access_token:
            raise HTTPException(
                status_code=403,
                detail=(
                    "To authenticate, click on the link: "
                    f"{self._get_auth_url()}"
                )
            )

        url = f"{self.api_url}{method}"
        headers = {"Content-Type": "application/json"}
        payload = {"auth": access_token}
        if params:
            payload.update(params)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        if "error" in data:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Bitrix API error: {data.get('error_description')}"
            )

        return data.get("result", data)

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
def get_bitrix_client(
    token_storage: TokenStorage = Depends(get_token_storage),
) -> Bitrix24Client:
    return Bitrix24Client(token_storage)
