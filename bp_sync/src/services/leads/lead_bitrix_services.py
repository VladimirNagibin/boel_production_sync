# from fastapi import Depends

from schemas.lead_schemas import LeadCreate, LeadUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient

# from ..bitrix_services.bitrix_api_client import BitrixAPIClient
# from ..dependencies import get_bitrix_client


class LeadBitrixClient(BaseBitrixEntityClient[LeadCreate, LeadUpdate]):
    entity_name = "lead"
    create_schema = LeadCreate
    update_schema = LeadUpdate


# def get_lead_bitrix_client(
#    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
# ) -> LeadBitrixClient:
#    return LeadBitrixClient(bitrix_client)
