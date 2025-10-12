from models.company_models import Company as CompanyDB

from ..base_services.base_service import BaseEntityClient
from .company_bitrix_services import (
    CompanyBitrixClient,
)
from .company_repository import CompanyRepository


class CompanyClient(
    BaseEntityClient[
        CompanyDB,
        CompanyRepository,
        CompanyBitrixClient,
    ]
):
    def __init__(
        self,
        company_bitrix_client: CompanyBitrixClient,
        company_repo: CompanyRepository,
    ):
        self._bitrix_client = company_bitrix_client
        self._repo = company_repo

    @property
    def entity_name(self) -> str:
        return "company"

    @property
    def bitrix_client(self) -> CompanyBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> CompanyRepository:
        return self._repo
