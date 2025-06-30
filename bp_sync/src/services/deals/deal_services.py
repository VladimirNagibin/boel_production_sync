from functools import lru_cache
from typing import Any

from fastapi import Depends

from .deal_bitrix_services import DealBitrixClient, get_deal_bitrix_client

# from core.logger import logger


class DealClient:
    def __init__(self, deal_bitrix_client: DealBitrixClient):
        self.deal_bitrix_client = deal_bitrix_client

    async def get_deal(self, deal_id: int) -> dict[Any, Any]:
        """Получение сделки по ID"""
        return await self.get_deal(deal_id)

    # async def create_deal(self, deal_data: dict) -> dict:
    #   """Создание новой сделки"""
    #    return await self.call_api("crm.deal.add", {"fields": deal_data})

    # async def update_deal(self, deal_id: int, deal_data: dict) -> dict:
    #    """Обновление сделки"""
    #    return await self.call_api(
    #        "crm.deal.update", {"id": deal_id, "fields": deal_data}
    #    )

    # async def list_deals(
    #    self, filter_params: dict = None, select: list = None
    # ) -> list:
    #    """Список сделок с фильтрацией"""
    #    params = {}
    #    if filter_params:
    #        params["filter"] = filter_params
    #    if select:
    #        params["select"] = select

    #    return await self.call_api("crm.deal.list", params)


@lru_cache()
def get_deal_client(
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
) -> DealClient:
    return DealClient(deal_bitrix_client)
