from functools import lru_cache

from fastapi import Depends

from schemas.deal_schemas import DealCreate

from .deal_bitrix_services import DealBitrixClient, get_deal_bitrix_client
from .deal_repository import DealRepository, get_deal_repository

# from core.logger import logger


class DealClient:
    def __init__(
        self,
        deal_bitrix_client: DealBitrixClient,
        deal_repo: DealRepository,
    ):
        self.deal_bitrix_client = deal_bitrix_client
        self.deal_repo = deal_repo

    async def get_deal(self, deal_id: int) -> DealCreate:
        """Получение сделки по ID"""
        return await self.deal_bitrix_client.get(deal_id)

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
    deal_repo: DealRepository = Depends(get_deal_repository),
) -> DealClient:
    return DealClient(deal_bitrix_client, deal_repo)
