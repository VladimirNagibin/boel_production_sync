import asyncio
import json
from typing import Any

from models.bases import EntityType
from schemas.timeline_comment_schemas import TimelineCommentCreate
from services.deals.deal_services import DealClient
from services.dependencies import reset_cache
from services.exceptions import ConflictException
from services.invoices.invoice_bitrix_services import InvoiceBitrixClient
from services.invoices.invoice_services import InvoiceClient
from services.rabbitmq_client import RabbitMQClient
from services.timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from services.timeline_comments.timeline_comment_repository import (
    TimelineCommentRepository,
)

DEALS_SLEEP_INTERVAL = 2


class DealProcessor:
    """Класс для обработки выгрузки сделок в БД"""

    def __init__(
        self,
        deal_client: DealClient,
        invoice_bitrix_client: InvoiceBitrixClient,
        invoice_client: InvoiceClient,
        timeline_client: TimeLineCommentBitrixClient,
        timeline_repo: TimelineCommentRepository,
        rabbitmq_client: RabbitMQClient,
    ):
        self.deal_client = deal_client
        self.invoice_bitrix_client = invoice_bitrix_client
        self.invoice_client = invoice_client
        self.timeline_client = timeline_client
        self.timeline_repo = timeline_repo
        self.rabbitmq_client = rabbitmq_client

    async def process_single_deal(self, deal_id: int) -> tuple[bool, str]:
        """Обработать одну сделку"""
        try:
            # Импорт сделки
            _, needs_refresh = await self.deal_client.import_from_bitrix(
                deal_id
            )
            await asyncio.sleep(DEALS_SLEEP_INTERVAL)

            if needs_refresh:
                reset_cache()
                await self.deal_client.import_from_bitrix(deal_id)

            # Обработка связанного инвойса
            await self._process_deal_invoice(deal_id)

            # Загрузка комментариев
            await self._load_deal_comments(deal_id)

            return True, "success"

        except Exception as e:
            return False, str(e)

    async def _process_deal_invoice(self, deal_id: int) -> None:
        """Обработать инвойс связанный со сделкой"""
        filter_entity = {"parentId2": deal_id}
        select = ["id"]

        invoice_result = await self.invoice_bitrix_client.list(
            select=select, filter_entity=filter_entity, start=0
        )

        if invoice_result.result:
            invoice_id = invoice_result.result[0].external_id
            if invoice_id:
                await self._send_invoice_to_queue(int(invoice_id))

    async def _send_invoice_to_queue(self, invoice_id: int) -> None:
        """Отправить информацию об инвойсе в RabbitMQ"""
        invoice, _ = await self.invoice_client.import_from_bitrix(invoice_id)

        message_data: dict[str, Any] = {
            "account_number": invoice.account_number,
            "invoice_id": invoice.external_id,
            "invoice_date": invoice.date_create.isoformat(),
            "company_id": invoice.company_id,
        }

        message = json.dumps(message_data).encode()
        await self.rabbitmq_client.send_message(message)

    async def _load_deal_comments(self, deal_id: int) -> None:
        """Загрузить комментарии сделки"""
        filter_entity: dict[str, Any] = {
            "ENTITY_TYPE": "deal",
            "ENTITY_ID": deal_id,
        }
        select = ["ID", "COMMENT", "CREATED", "AUTHOR_ID"]

        comments_result = await self.timeline_client.list(
            select=select, filter_entity=filter_entity, start=0
        )

        if comments_result.result:
            for comment in comments_result.result:
                await self._save_timeline_comment(comment, deal_id)

    async def _save_timeline_comment(
        self, comment_data: Any, deal_id: int
    ) -> None:
        """Сохранить комментарий временной линии"""
        comment_data.entity_id = deal_id
        comment_data.entity_type = EntityType.DEAL

        timeline_create = TimelineCommentCreate(
            **comment_data.model_dump(by_alias=True, exclude_unset=True)
        )

        try:
            await self.timeline_repo.create_entity(timeline_create)
        except ConflictException:
            await self.timeline_repo.update_entity(timeline_create)
