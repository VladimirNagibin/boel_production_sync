# from fastapi import Depends

from models.contact_models import Contact as ContactDB

from ..base_services.base_service import BaseEntityClient
from .contact_bitrix_services import (  # get_contact_bitrix_client,
    ContactBitrixClient,
)
from .contact_repository import ContactRepository  # , get_contact_repository


class ContactClient(
    BaseEntityClient[ContactDB, ContactRepository, ContactBitrixClient]
):
    def __init__(
        self,
        contact_bitrix_client: ContactBitrixClient,
        contact_repo: ContactRepository,
    ):
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


# def get_contact_client(
#    contact_bitrix_client: ContactBitrixClient = Depends(
#        get_contact_bitrix_client
#    ),
#    contact_repo: ContactRepository = Depends(get_contact_repository),
# ) -> ContactClient:
#    return ContactClient(contact_bitrix_client, contact_repo)
