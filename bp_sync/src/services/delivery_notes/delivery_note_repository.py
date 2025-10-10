from typing import Any, Callable, Coroutine, Type

from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base
from models.company_models import Company as CompanyDB
from models.delivery_note_models import DeliveryNote as DeliveryNoteDB
from models.invoice_models import Invoice as InvoiceDB
from models.references import ShippingCompany, Warehouse
from models.user_models import User as UserDB
from schemas.delivery_note_schemas import (
    DeliveryNoteCreate,
    DeliveryNoteUpdate,
)

from ..base_repositories.base_repository import BaseRepository
from ..companies.company_services import CompanyClient
from ..invoices.invoice_services import InvoiceClient
from ..users.user_services import UserClient


class DeliveryNoteRepository(
    BaseRepository[DeliveryNoteDB, DeliveryNoteCreate, DeliveryNoteUpdate, str]
):

    model = DeliveryNoteDB

    def __init__(
        self,
        session: AsyncSession,
        get_company_client: Callable[[], Coroutine[Any, Any, CompanyClient]],
        get_invoice_client: Callable[[], Coroutine[Any, Any, InvoiceClient]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
    ):
        super().__init__(session)
        self.get_company_client = get_company_client
        self.get_invoice_client = get_invoice_client
        self.get_user_client = get_user_client

    async def create_entity(self, data: DeliveryNoteCreate) -> DeliveryNoteDB:
        """Создает новую накладную с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: DeliveryNoteCreate | DeliveryNoteUpdate
    ) -> DeliveryNoteDB:
        """Обновляет существующую накладную"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("shipping_company_id", ShippingCompany, "external_id"),
            ("warehouse_id", Warehouse, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        company_client = await self.get_company_client()
        invoice_client = await self.get_invoice_client()
        user_client = await self.get_user_client()
        return {
            "company_id": (company_client, CompanyDB, False),
            "assigned_by_id": (user_client, UserDB, False),
            "invoice_id": (invoice_client, InvoiceDB, False),
        }
