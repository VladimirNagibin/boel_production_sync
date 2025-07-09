from fastapi import Depends

from models.lead_models import Lead as LeadDB

from .lead_bitrix_services import LeadBitrixClient, get_lead_bitrix_client
from .lead_repository import LeadRepository, get_lead_repository

# from core.logger import logger


class LeadClient:
    def __init__(
        self,
        lead_bitrix_client: LeadBitrixClient,
        lead_repo: LeadRepository,
    ):
        self.lead_bitrix_client = lead_bitrix_client
        self.lead_repo = lead_repo

    async def create_lead_from_bitrix_to_bd(self, lead_id: int) -> LeadDB:
        """Получение сделки по ID"""
        lead_create = await self.lead_bitrix_client.get(lead_id)
        lead_db = await self.lead_repo.create_lead(lead_create)
        return lead_db

    async def update_lead_from_bitrix_to_bd(self, lead_id: int) -> LeadDB:
        """Получение сделки по ID"""
        lead_create = await self.lead_bitrix_client.get(lead_id)
        lead_db = await self.lead_repo.update_lead(lead_create)
        return lead_db


def get_lead_client(
    lead_bitrix_client: LeadBitrixClient = Depends(get_lead_bitrix_client),
    lead_repo: LeadRepository = Depends(get_lead_repository),
) -> LeadClient:
    return LeadClient(lead_bitrix_client, lead_repo)
