from fastapi import Depends

from schemas.company_schemas import CompanyCreate, CompanyUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..dependencies import get_bitrix_client


class CompanyBitrixClient(
    BaseBitrixEntityClient[CompanyCreate, CompanyUpdate]
):
    entity_name = "company"
    create_schema = CompanyCreate
    update_schema = CompanyUpdate


def get_company_bitrix_client(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
) -> CompanyBitrixClient:
    return CompanyBitrixClient(bitrix_client)
