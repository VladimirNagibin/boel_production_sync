# from fastapi import Depends

from models.deal_models import Deal as DealDB

from ..base_services.base_service import BaseEntityClient
from .deal_bitrix_services import DealBitrixClient  # , get_deal_bitrix_client
from .deal_repository import DealRepository  # , get_deal_repository


class DealClient(BaseEntityClient[DealDB, DealRepository, DealBitrixClient]):
    def __init__(
        self,
        deal_bitrix_client: DealBitrixClient,
        deal_repo: DealRepository,
    ):
        self._bitrix_client = deal_bitrix_client
        self._repo = deal_repo

    @property
    def entity_name(self) -> str:
        return "deal"

    @property
    def bitrix_client(self) -> DealBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> DealRepository:
        return self._repo


# def get_deal_client(
#    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
#    deal_repo: DealRepository = Depends(get_deal_repository),
# ) -> DealClient:
#    return DealClient(deal_bitrix_client, deal_repo)
