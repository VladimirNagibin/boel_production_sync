from fastapi import Depends

from models.company_models import Company as CompanyDB

from ..base_services.base_service import BaseEntityClient
from .company_bitrix_services import (
    CompanyBitrixClient,
    get_company_bitrix_client,
)
from .company_repository import CompanyRepository, get_company_repository


class CompanyClient(
    BaseEntityClient[
        CompanyDB,
        CompanyRepository,
        CompanyBitrixClient,
    ]
):
    def __init__(
        self,
        contact_bitrix_client: CompanyBitrixClient,
        contact_repo: CompanyRepository,
    ):
        self._bitrix_client = contact_bitrix_client
        self._repo = contact_repo

    @property
    def entity_name(self) -> str:
        return "company"

    @property
    def bitrix_client(self) -> CompanyBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> CompanyRepository:
        return self._repo


def get_company_client(
    company_bitrix_client: CompanyBitrixClient = Depends(
        get_company_bitrix_client
    ),
    company_repo: CompanyRepository = Depends(get_company_repository),
) -> CompanyClient:
    return CompanyClient(company_bitrix_client, company_repo)
