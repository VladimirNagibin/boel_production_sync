from typing import TYPE_CHECKING, Any

# from core.logger import logger
from schemas.deal_schemas import DealCreate
from schemas.invoice_schemas import InvoiceCreate

from .enums import InvoiceStage

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
            self.deal_client.update_tracker.update_field(
                "company_id", invoice.company_id, deal_b24
            )

        if invoice.closedate and (
            (not deal_b24.payment_deadline)
            or deal_b24.payment_deadline != invoice.closedate
        ):
            self.deal_client.update_tracker.update_field(
                "payment_deadline", invoice.closedate, deal_b24
            )

        if invoice.payment_grace_period is not None and (
            (deal_b24.payment_grace_period is None)
            or deal_b24.payment_grace_period != invoice.payment_grace_period
        ):
            self.deal_client.update_tracker.update_field(
                "payment_grace_period", invoice.payment_grace_period, deal_b24
            )

        ship = None
        if invoice.shipping_company_id:
            try:
                deal_repo = self.deal_client.repo
                company_client = await deal_repo.get_company_client()
                ship = await company_client.repo.get_ext_alt_id_by_external_id(
                    invoice.shipping_company_id
                )
            except Exception:
                ...
        if invoice.shipping_company_id and (
            (not deal_b24.shipping_company_id)
            or ship != deal_b24.shipping_company_id
        ):
            self.deal_client.update_tracker.update_field(
                "shipping_company_id", ship, deal_b24
            )

        if invoice.payment_type and (
            (not deal_b24.payment_type)
            or deal_b24.payment_type != invoice.payment_type
        ):
            self.deal_client.update_tracker.update_field(
                "payment_type", invoice.payment_type, deal_b24
            )

        if invoice.invoice_stage_id in (InvoiceStage.NEW, InvoiceStage.SEND):
            ...

        return True
