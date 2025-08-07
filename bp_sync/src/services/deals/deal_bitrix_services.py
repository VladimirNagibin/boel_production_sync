# from fastapi import Depends

from schemas.deal_schemas import DealCreate, DealUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient

# from ..bitrix_services.bitrix_api_client import BitrixAPIClient
# from ..dependencies import get_bitrix_client


class DealBitrixClient(BaseBitrixEntityClient[DealCreate, DealUpdate]):
    entity_name = "deal"
    create_schema = DealCreate
    update_schema = DealUpdate


# def get_deal_bitrix_client(
#    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
# ) -> DealBitrixClient:
#    return DealBitrixClient(bitrix_client)
