from typing import TYPE_CHECKING, Any

# from core.logger import logger
from models.enums import StageSemanticEnum
from schemas.deal_schemas import DealCreate
from schemas.invoice_schemas import InvoiceCreate

from .enums import InvoiceStage

if TYPE_CHECKING:
    from .deal_services import DealClient

DEAL_STAGE_INVOICE = "FINAL_INVOICE"
DEAL_STAGE_LOSE = "LOSE"
DEAL_STAGE_APOLOGY = "APOLOGY"
DEAL_STAGE_FOR_SHIPMENT = "1"
DEAL_STAGE_WON = "WON"


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

        await self.deal_client.check_source(deal_b24, deal_db)

        if invoice.company_id and (
            (not deal_b24.company_id)
            or deal_b24.company_id != invoice.company_id
        ):
            self.deal_client.update_tracker.update_field(
                "company_id", invoice.company_id, deal_b24
            )

        if invoice.contact_id and (
            (not deal_b24.contact_id)
            or deal_b24.contact_id != invoice.contact_id
        ):
            self.deal_client.update_tracker.update_field(
                "contact_id", invoice.contact_id, deal_b24
            )

        if not invoice.contact_id and deal_b24.contact_id:
            self.deal_client.update_tracker.update_field(
                "contact_id", 0, deal_b24
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
            if deal_b24.stage_id and deal_b24.stage_id != DEAL_STAGE_INVOICE:
                self.deal_client.update_tracker.update_field(
                    "stage_id", DEAL_STAGE_INVOICE, deal_b24
                )

            if (
                deal_b24.current_stage_id
                and deal_b24.current_stage_id != DEAL_STAGE_INVOICE
            ):
                self.deal_client.update_tracker.update_field(
                    "current_stage_id", DEAL_STAGE_INVOICE, deal_b24
                )

        if invoice.invoice_stage_id == InvoiceStage.FAIL:
            if deal_b24.stage_semantic_id and (
                deal_b24.stage_semantic_id != StageSemanticEnum.FAIL
            ):
                self.deal_client.update_tracker.update_field(
                    "stage_id", DEAL_STAGE_LOSE, deal_b24
                )
                self.deal_client.update_tracker.update_field(
                    "current_stage_id", DEAL_STAGE_LOSE, deal_b24
                )

        product_client = self.deal_client.product_bitrix_client
        if deal_b24.external_id and invoice.external_id:
            if not await product_client.update_deal_product_from_invoice(
                int(deal_b24.external_id), int(invoice.external_id)
            ):
                # TODO: unsuccessful processing of products
                ...
        if invoice.invoice_stage_id == InvoiceStage.SECCESS:
            # TODO: handel seccess stage
            # Checking the conditions that the deal is successful
            # and transform in stage WON
            # Else in stage for SHIPMENT or FAIL
            if (
                deal_b24.stage_id == DEAL_STAGE_FOR_SHIPMENT
                and deal_db
                and deal_db.stage_id == DEAL_STAGE_WON
            ):
                self.deal_client.update_tracker.update_field(
                    "stage_id", DEAL_STAGE_WON, deal_b24
                )
                self.deal_client.update_tracker.update_field(
                    "current_stage_id", DEAL_STAGE_WON, deal_b24
                )
            # The edit at the shipping stage has not yet been implemented
            if (
                deal_b24.stage_id == DEAL_STAGE_WON
                and deal_db
                and deal_db.stage_id in (DEAL_STAGE_LOSE, DEAL_STAGE_APOLOGY)
            ):
                self.deal_client.update_tracker.update_field(
                    "stage_id", deal_db.stage_id, deal_b24
                )
                self.deal_client.update_tracker.update_field(
                    "current_stage_id", deal_db.stage_id, deal_b24
                )
                await self.deal_client.move_invoice_in_fail_stage_1s(invoice)
            if deal_b24.stage_id not in (
                DEAL_STAGE_FOR_SHIPMENT,
                DEAL_STAGE_WON,
            ):
                # The invoice cannot be successful and
                # the deal is not on shipment or is not successful.
                ...

        return True
