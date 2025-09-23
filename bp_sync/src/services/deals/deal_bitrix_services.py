from schemas.deal_schemas import DealCreate, DealUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class DealBitrixClient(BaseBitrixEntityClient[DealCreate, DealUpdate]):
    entity_name = "deal"
    create_schema = DealCreate
    update_schema = DealUpdate
