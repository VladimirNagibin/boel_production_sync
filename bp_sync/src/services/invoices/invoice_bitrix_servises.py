from fastapi import Depends

from schemas.invoice_schemas import InvoiceCreate, InvoiceUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..dependencies import get_bitrix_client


class InvoiceBitrixClient(
    BaseBitrixEntityClient[InvoiceCreate, InvoiceUpdate]
):
    entity_name = "invoice"
    create_schema = InvoiceCreate
    update_schema = InvoiceUpdate


def get_invoice_bitrix_client(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
) -> InvoiceBitrixClient:
    return InvoiceBitrixClient(bitrix_client)
