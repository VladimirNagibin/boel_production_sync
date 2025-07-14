from fastapi import Depends

from models.lead_models import Lead as LeadDB

from ..base_services.base_service import BaseEntityClient
from .lead_bitrix_services import LeadBitrixClient, get_lead_bitrix_client
from .lead_repository import LeadRepository, get_lead_repository


class LeadClient(BaseEntityClient[LeadDB, LeadRepository, LeadBitrixClient]):
    def __init__(
        self,
        lead_bitrix_client: LeadBitrixClient,
        lead_repo: LeadRepository,
    ):
        self._bitrix_client = lead_bitrix_client
        self._repo = lead_repo

    @property
    def entity_name(self) -> str:
        return "lead"

    @property
    def bitrix_client(self) -> LeadBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> LeadRepository:
        return self._repo


def get_lead_client(
    lead_bitrix_client: LeadBitrixClient = Depends(get_lead_bitrix_client),
    lead_repo: LeadRepository = Depends(get_lead_repository),
) -> LeadClient:
    return LeadClient(lead_bitrix_client, lead_repo)
