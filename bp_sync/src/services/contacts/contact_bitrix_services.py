from fastapi import Depends

from schemas.contact_schemas import ContactCreate, ContactUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..dependencies import get_bitrix_client


class ContactBitrixClient(
    BaseBitrixEntityClient[ContactCreate, ContactUpdate]
):
    entity_name = "contact"
    create_schema = ContactCreate
    update_schema = ContactUpdate


def get_contact_bitrix_client(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
) -> ContactBitrixClient:
    return ContactBitrixClient(bitrix_client)
