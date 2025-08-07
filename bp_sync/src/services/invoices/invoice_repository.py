from typing import Any, Callable, Coroutine, Type

# from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base  # , get_session
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.deal_models import Deal as DealDB
from models.invoice_models import Invoice as InvoiceDB
from models.references import (
    CreationSource,
    Currency,
    DealFailureReason,
    DealType,
    InvoiceStage,
    MainActivity,
    ShippingCompany,
    Source,
    Warehouse,
)
from models.user_models import User as UserDB
from schemas.invoice_schemas import InvoiceCreate, InvoiceUpdate

from ..base_repositories.base_repository import BaseRepository
from ..companies.company_services import CompanyClient  # , get_company_client
from ..contacts.contact_services import ContactClient  # , get_contact_client
from ..deals.deal_services import DealClient  # , get_deal_client
from ..users.user_services import UserClient  # , get_user_client


class InvoiceRepository(
    BaseRepository[InvoiceDB, InvoiceCreate, InvoiceUpdate]
):

    model = InvoiceDB
    entity_type = EntityType.INVOICE

    def __init__(
        self,
        session: AsyncSession,
        # company_client: "CompanyClient",
        # contact_client: "ContactClient",
        # deal_client: "DealClient",
        # user_client: UserClient,
        get_company_client: Callable[[], Coroutine[Any, Any, CompanyClient]],
        get_contact_client: Callable[[], Coroutine[Any, Any, ContactClient]],
        get_deal_client: Callable[[], Coroutine[Any, Any, DealClient]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
    ):
        super().__init__(session)
        self.get_company_client = get_company_client
        self.get_contact_client = get_contact_client
        self.get_deal_client = get_deal_client
        self.get_user_client = get_user_client

    async def create_entity(self, data: InvoiceCreate) -> InvoiceDB:
        """Создает новый контакт с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: InvoiceCreate | InvoiceUpdate
    ) -> InvoiceDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("currency_id", Currency, "external_id"),
            ("invoice_stage_id", InvoiceStage, "external_id"),
            ("previous_stage_id", InvoiceStage, "external_id"),
            ("current_stage_id", InvoiceStage, "external_id"),
            ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt4_id"),
            ("warehouse_id", Warehouse, "ext_alt_id"),
            ("creation_source_id", CreationSource, "ext_alt_id"),
            ("invoice_failure_reason_id", DealFailureReason, "ext_alt4_id"),
            ("shipping_company_id", ShippingCompany, "external_id"),
            ("type_id", DealType, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        company_client = await self.get_company_client()
        contact_client = await self.get_contact_client()
        user_client = await self.get_user_client()
        deal_client = await self.get_deal_client()
        return {
            "contact_id": (contact_client, ContactDB, False),
            "company_id": (company_client, CompanyDB, False),
            "deal_id": (deal_client, DealDB, False),
            "assigned_by_id": (user_client, UserDB, True),
            "created_by_id": (user_client, UserDB, True),
            "modify_by_id": (user_client, UserDB, False),
            "last_activity_by": (user_client, UserDB, False),
            "moved_by_id": (user_client, UserDB, False),
        }


# def get_invoice_repository(
#    session: AsyncSession = Depends(get_session),
#    company_client: CompanyClient = Depends(get_company_client),
#    contact_client: ContactClient = Depends(get_contact_client),
#    deal_client: DealClient = Depends(get_deal_client),
#    user_client: UserClient = Depends(get_user_client),
# ) -> InvoiceRepository:

#    return InvoiceRepository(
#        session=session,
#        company_client=company_client,
#        contact_client=contact_client,
#        deal_client=deal_client,
#        user_client=user_client,
#    )
