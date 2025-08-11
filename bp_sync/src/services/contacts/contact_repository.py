from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine, Type

# from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base  # , get_session
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.lead_models import Lead as LeadDB
from models.references import (
    ContactType,
    DealFailureReason,
    DealType,
    MainActivity,
    Source,
)
from models.user_models import User as UserDB
from schemas.contact_schemas import ContactCreate, ContactUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)
from ..users.user_services import UserClient  # , get_user_client

if TYPE_CHECKING:
    from ..companies.company_services import CompanyClient
    from ..entities.source_services import SourceClient
    from ..leads.lead_services import LeadClient


class ContactRepository(
    EntityWithCommunicationsRepository[
        ContactDB, ContactCreate, ContactUpdate, int
    ]
):

    model = ContactDB
    entity_type = EntityType.CONTACT

    def __init__(
        self,
        session: AsyncSession,
        # company_client: "CompanyClient",
        # lead_client: "LeadClient",
        # user_client: UserClient,
        get_company_client: Callable[[], Coroutine[Any, Any, CompanyClient]],
        get_lead_client: Callable[[], Coroutine[Any, Any, LeadClient]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
        get_source_client: Callable[[], Coroutine[Any, Any, SourceClient]],
    ):
        super().__init__(session)
        self.get_company_client = get_company_client
        self.get_lead_client = get_lead_client
        self.get_user_client = get_user_client
        self.get_source_client = get_source_client

    async def create_entity(self, data: ContactCreate) -> ContactDB:
        """Создает новый контакт с проверкой связанных объектов"""
        # data_without_entity = ContactCreate(**data.model_dump())
        # data_without_entity.company_id = None
        # data_without_entity.lead_id = None
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)
        # return await self.update_entity(data)

    async def update_entity(
        self, data: ContactCreate | ContactUpdate
    ) -> ContactDB:
        """Обновляет существующий контакт"""
        # data.company_id = None
        # data.lead_id = None
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("type_id", ContactType, "external_id"),
            # ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt2_id"),
            ("deal_failure_reason_id", DealFailureReason, "ext_alt2_id"),
            ("deal_type_id", DealType, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        company_client = await self.get_company_client()
        lead_client = await self.get_lead_client()
        user_client = await self.get_user_client()
        source_client = await self.get_source_client()
        return {
            "lead_id": (lead_client, LeadDB, False),
            "company_id": (company_client, CompanyDB, False),
            "assigned_by_id": (user_client, UserDB, True),
            "created_by_id": (user_client, UserDB, True),
            "modify_by_id": (user_client, UserDB, False),
            "last_activity_by": (user_client, UserDB, False),
            "source_id": (source_client, Source, False),
        }


# def get_contact_repository(
#    session: AsyncSession = Depends(get_session),
#    user_client: UserClient = Depends(get_user_client),
# company_client: "CompanyClient" = Depends(lambda: get_company_client()),
# lead_client: "LeadClient" = Depends(lambda: get_lead_client()),
# ) -> ContactRepository:
#    from ..companies.company_services import get_company_client
#    from ..leads.lead_services import get_lead_client
#    company_client = get_company_client(session)
#    lead_client = get_lead_client(session)
#    return ContactRepository(
#        session=session,
#        company_client=company_client,  # Depends(get_company_client),
#        lead_client=lead_client,  # Depends(get_lead_client),
#        user_client=user_client,
#    )
