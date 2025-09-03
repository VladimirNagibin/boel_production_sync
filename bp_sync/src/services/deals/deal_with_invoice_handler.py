from typing import TYPE_CHECKING, Any

# from core.logger import logger
from schemas.deal_schemas import DealCreate
from schemas.invoice_schemas import InvoiceCreate

if TYPE_CHECKING:
    from .deal_services import DealClient


class DealWithInvioceHandler:
    """Обработчик стадий сделки"""

    def __init__(self, deal_client: "DealClient"):
        self.deal_client = deal_client

    async def handle_deal_with_invoice(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        invoice: InvoiceCreate,
        changes: dict[str, dict[str, Any]] | None,
    ) -> bool:
        # TODO: Реализовать логику обработки сделки с выставленным счётом
        if invoice.company_id and (
            (not deal_b24.company_id)
            or deal_b24.company_id != invoice.company_id
        ):
            ...

        return True
