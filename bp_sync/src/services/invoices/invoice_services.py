import requests  # type: ignore[import-untyped]

from core.logger import logger
from core.settings import settings
from models.invoice_models import Invoice as InvoiceDB

from ..base_services.base_service import BaseEntityClient
from .invoice_bitrix_services import (
    InvoiceBitrixClient,
)
from .invoice_repository import InvoiceRepository


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

    def send_invoice_request_to_fail(self, invoice_id: int) -> bool:
        """
        Отправляет запрос к сервису для пометки счёта на удаление
        """
        url = (
            f"{settings.WEB_HOOK_PORTAL}/"
            f"{settings.ENDPOINT_SERND_FAIL_INVOICE}?"
            f"id_invoice={invoice_id}&key={settings.WEB_HOOK_KEY}"
        )

        try:
            logger.info(f"Отправка запроса для invoice_id: {invoice_id}")
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                logger.info(f"Успешный ответ от сервера: {response.text}")
                return True
            else:
                logger.error(f"Ошибка сервера: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при отправке запроса: {e}")
            return False
