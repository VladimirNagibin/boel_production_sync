from typing import Any

from core.settings import settings
from models.contact_models import Contact as ContactDB

from ..base_services.base_service import BaseEntityClient
from .contact_bitrix_services import (
    ContactBitrixClient,
)
from .contact_repository import ContactRepository


class ContactClient(
    BaseEntityClient[ContactDB, ContactRepository, ContactBitrixClient]
):
    def __init__(
        self,
        contact_bitrix_client: ContactBitrixClient,
        contact_repo: ContactRepository,
    ):
        super().__init__()
        self._bitrix_client = contact_bitrix_client
        self._repo = contact_repo

    @property
    def entity_name(self) -> str:
        return "contact"

    @property
    def bitrix_client(self) -> ContactBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> ContactRepository:
        return self._repo

    @property
    def webhook_config(self) -> dict[str, Any]:
        return settings.web_hook_config_contact
