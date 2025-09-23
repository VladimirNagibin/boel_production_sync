from typing import Any

from schemas.base_schemas import ListResponseSchema
from schemas.invoice_schemas import InvoiceCreate, InvoiceUpdate

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient

ENTITY_TYPE_ID = 31


class InvoiceBitrixClient(
    BaseBitrixEntityClient[InvoiceCreate, InvoiceUpdate]
):
    entity_name = "invoice"
    create_schema = InvoiceCreate
    update_schema = InvoiceUpdate

    async def create(
        self,
        data: InvoiceUpdate,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> int | None:
        return await super().create(data, ENTITY_TYPE_ID)

    async def get(
        self,
        entity_id: int | str,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> InvoiceCreate:
        return await super().get(entity_id, ENTITY_TYPE_ID)

    async def update(
        self,
        data: InvoiceUpdate,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> bool:
        return await super().update(data, ENTITY_TYPE_ID)

    async def delete(
        self,
        entity_id: int | str,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> bool:
        return await super().delete(entity_id, ENTITY_TYPE_ID)

    async def list(
        self,
        select: list[str] | None = None,
        filter_entity: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        start: int = 0,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> ListResponseSchema[InvoiceUpdate]:
        return await super().list(
            select, filter_entity, order, start, ENTITY_TYPE_ID
        )

    async def get_invoice_by_deal_id(
        self,
        deal_id: int,
    ) -> InvoiceCreate | None:
        invoices = await self.list(
            select=["id"], filter_entity={"parentId2": deal_id}
        )
        if invoices and invoices.result:
            id_invoice = invoices.result[0].external_id
            if id_invoice:
                return await self.get(id_invoice)
        return None
