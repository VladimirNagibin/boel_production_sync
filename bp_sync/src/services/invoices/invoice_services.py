# from fastapi import Depends

from models.invoice_models import Invoice as InvoiceDB

from ..base_services.base_service import BaseEntityClient
from .invoice_bitrix_services import (  # get_invoice_bitrix_client,
    InvoiceBitrixClient,
)
from .invoice_repository import InvoiceRepository  # , get_invoice_repository


class InvoiceClient(
    BaseEntityClient[InvoiceDB, InvoiceRepository, InvoiceBitrixClient]
):
    def __init__(
        self,
        invoice_bitrix_client: InvoiceBitrixClient,
        invoice_repo: InvoiceRepository,
    ):
        self._bitrix_client = invoice_bitrix_client
        self._repo = invoice_repo

    @property
    def entity_name(self) -> str:
        return "invoice"

    @property
    def bitrix_client(self) -> InvoiceBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> InvoiceRepository:
        return self._repo


# def get_invoice_client(
#    invoice_bitrix_client: InvoiceBitrixClient = Depends(
#        get_invoice_bitrix_client
#    ),
#    invoice_repo: InvoiceRepository = Depends(get_invoice_repository),
# ) -> InvoiceClient:
#    return InvoiceClient(invoice_bitrix_client, invoice_repo)
