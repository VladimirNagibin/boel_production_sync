from functools import lru_cache
from typing import Any

from fastapi import Depends

from core.logger import logger

from .bitrix_api_client import BitrixAPIClient
from .bitrix_dependencies import get_bitrix_client


class BitrixAPIClient1:
    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    # Примеры конкретных методов API
    async def get_deal(self, deal_id: int) -> dict[Any, Any]:
        """Получение сделки по ID"""
        return await self.bitrix_client.call_api(
            "crm.deal.get", {"id": deal_id}
        )

    async def create_deal(self, deal_data: dict) -> dict:
        """Создание новой сделки"""
        return await self.call_api("crm.deal.add", {"fields": deal_data})

    async def update_deal(self, deal_id: int, deal_data: dict) -> dict:
        """Обновление сделки"""
        return await self.call_api(
            "crm.deal.update", {"id": deal_id, "fields": deal_data}
        )

    async def list_deals(
        self, filter_params: dict = None, select: list = None
    ) -> list:
        """Список сделок с фильтрацией"""
        params = {}
        if filter_params:
            params["filter"] = filter_params
        if select:
            params["select"] = select

        return await self.call_api("crm.deal.list", params)


@lru_cache()
def get_bitrix_client1(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
) -> BitrixAPIClient1:
    return BitrixAPIClient1(bitrix_client)
