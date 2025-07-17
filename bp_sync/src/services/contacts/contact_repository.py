from typing import Any, Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base, get_session
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
from ..companies.company_services import CompanyClient, get_company_client
from ..leads.lead_services import LeadClient, get_lead_client
from ..users.user_services import UserClient, get_user_client


class ContactRepository(
    EntityWithCommunicationsRepository[ContactDB, ContactCreate, ContactUpdate]
):

    model = ContactDB
    entity_type = EntityType.CONTACT

    def __init__(
        self,
        session: AsyncSession,
        company_client: CompanyClient,
        lead_client: LeadClient,
        user_client: UserClient,
    ):
        super().__init__(session)
        self.company_client = company_client
        self.lead_client = lead_client
        self.user_client = user_client

    async def create_entity(self, data: ContactCreate) -> ContactDB:
        """Создает новый контакт с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: ContactCreate | ContactUpdate
    ) -> ContactDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("type_id", ContactType, "external_id"),
            ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt2_id"),
            ("deal_failure_reason_id", DealFailureReason, "ext_alt2_id"),
            ("deal_type_id", DealType, "external_id"),
        ]

    def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return {
            "lead_id": (self.lead_client, LeadDB, False),
            "company_id": (self.company_client, CompanyDB, False),
            "assigned_by_id": (self.user_client, UserDB, True),
            "created_by_id": (self.user_client, UserDB, True),
            "modify_by_id": (self.user_client, UserDB, False),
            "last_activity_by": (self.user_client, UserDB, False),
        }


def get_contact_repository(
    session: AsyncSession = Depends(get_session),
    company_client: CompanyClient = Depends(get_company_client),
    lead_client: LeadClient = Depends(get_lead_client),
    user_client: UserClient = Depends(get_user_client),
) -> ContactRepository:
    return ContactRepository(
        session=session,
        company_client=company_client,
        lead_client=lead_client,
        user_client=user_client,
    )
