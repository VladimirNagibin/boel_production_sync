import os
import httpx
from datetime import datetime, timedelta
from fastapi import HTTPException

from core.settings import settings


class Bitrix24Client:
    def __init__(self):
        self.client_id = settings.BITRIX_CLIENT_ID
        self.client_secret = settings.BITRIX_CLIENT_SECRET
        self.redirect_uri = settings.BITRIX_REDIRECT_URI
        self.bitrix_domain = settings.BITRIX_PORTAL
        self.token_url = f"{self.bitrix_domain}/oauth/token/"
        self.api_url = f"{self.bitrix_domain}/rest/"
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def get_auth_code(self) -> str:
        ...

    def get_auth_url(self, state: str | None = None) -> str:
        """Генерация URL для авторизации в Bitrix24"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "crm,user,task"
        }
        if state:
            params["state"] = state

        return f"{self.bitrix_domain}/oauth/authorize/?{'&'.join(f'{k}={v}' for k,v in params.items())}"

    async def fetch_token(self, code: str) -> dict:
        """Получение токена по коду авторизации"""
        params = {
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
            raise HTTPException(
                status_code=400,
                detail=f"Auth failed: {token_data.get('error_description')}"
            )

        self._store_tokens(token_data)
        return token_data

    async def refresh_access_token(self) -> dict:
        """Обновление токена доступа"""
        if not self.refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.token_url, params=params)
            token_data = response.json()

        if "error" in token_data:
            raise HTTPException(
                status_code=401,
                detail=f"Token refresh failed: {token_data.get('error_description')}"
            )

        self._store_tokens(token_data)
        return token_data

    def _store_tokens(self, token_data: dict):
        """Сохранение полученных токенов"""
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])

    def is_token_expired(self) -> bool:
        """Проверка истечения срока действия токена"""
        return datetime.now() >= self.expires_at if self.expires_at else True

    async def call_api(
        self, 
        method: str, 
        params: dict = None, 
        retry: bool = True
    ) -> dict:
        """
        Отправка API запроса к Bitrix24

        :param method: API метод (например 'crm.deal.list')
        :param params: Параметры запроса
        :param retry: Повторять запрос после обновления токена при необходимости
        """
        if not self.access_token or self.is_token_expired():
            if self.refresh_token:
                await self.refresh_access_token()
            else:
                raise HTTPException(status_code=401, detail="Not authenticated")

        url = f"{self.api_url}{method}"
        headers = {"Content-Type": "application/json"}
        payload = {"auth": self.access_token}
        if params:
            payload.update(params)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()

        # Обработка истекшего токена
        if retry and "error" in data and data["error"] == "expired_token":
            await self.refresh_access_token()
            return await self.call_api(method, params, retry=False)

        if "error" in data:
            raise HTTPException(
                status_code=400,
                detail=f"Bitrix API error: {data.get('error_description')}"
            )

        return data.get("result", data)

    # Примеры конкретных методов API
    async def get_deal(self, deal_id: int) -> dict:
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