from typing import Any

from fastapi import Depends

from schemas.base_schemas import ListResponseSchema
from schemas.invoice_schemas import InvoiceCreate, InvoiceUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..dependencies import get_bitrix_client

ENTITY_TYPE_ID = 31


class InvoiceBitrixClient(
    BaseBitrixEntityClient[InvoiceCreate, InvoiceUpdate]
):
    entity_name = "invoice"
    create_schema = InvoiceCreate
    update_schema = InvoiceUpdate

    async def create(
        self, data: InvoiceUpdate, entity_type_id: int | None = None
    ) -> int | None:
        return await super().create(data, ENTITY_TYPE_ID)

    async def get(
        self, entity_id: int, entity_type_id: int | None = None
    ) -> InvoiceCreate:
        return await super().get(entity_id, ENTITY_TYPE_ID)

    async def update(
        self, data: InvoiceUpdate, entity_type_id: int | None = None
    ) -> bool:
        return await super().update(data, ENTITY_TYPE_ID)

    async def delete(
        self, entity_id: int, entity_type_id: int | None = None
    ) -> bool:
        return await super().delete(entity_id, ENTITY_TYPE_ID)

    async def list(
        self,
        select: list[str] | None = None,
        filter_entity: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        start: int = 0,
        entity_type_id: int | None = None,
    ) -> ListResponseSchema[InvoiceUpdate]:
        return await super().list(
            select, filter_entity, order, start, ENTITY_TYPE_ID
        )


def get_invoice_bitrix_client(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
) -> InvoiceBitrixClient:
    return InvoiceBitrixClient(bitrix_client)
