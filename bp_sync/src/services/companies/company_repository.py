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
    Currency,
    DealFailureReason,
    DealType,
    Emploees,
    Industry,
    MainActivity,
    ShippingCompany,
    Source,
)
from models.user_models import User as UserDB
from schemas.company_schemas import CompanyCreate, CompanyUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)
from ..contacts.contact_services import ContactClient, get_contact_client
from ..leads.lead_services import LeadClient, get_lead_client
from ..users.user_services import UserClient, get_user_client


class CompanyRepository(
    EntityWithCommunicationsRepository[CompanyDB, CompanyCreate, CompanyUpdate]
):

    model = CompanyDB
    entity_type = EntityType.COMPANY

    def __init__(
        self,
        session: AsyncSession,
        contact_client: ContactClient,
        lead_client: LeadClient,
        user_client: UserClient,
    ):
        super().__init__(session)
        self.contact_client = contact_client
        self.lead_client = lead_client
        self.user_client = user_client

    async def create_entity(self, data: CompanyCreate) -> CompanyDB:
        """Создает новый контакт с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: CompanyCreate | CompanyUpdate
    ) -> CompanyDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("currency_id", Currency, "external_id"),
            ("company_type_id", ContactType, "external_id"),
            ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt3_id"),
            ("deal_failure_reason_id", DealFailureReason, "ext_alt3_id"),
            ("deal_type_id", DealType, "external_id"),
            ("shipping_company_id", ShippingCompany, "ext_alt_id"),
            ("industry_id", Industry, "external_id"),
            ("employees_id", Emploees, "external_id"),
        ]

    def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return {
            "lead_id": (self.lead_client, LeadDB, False),
            "contact_id": (self.contact_client, ContactDB, False),
            "assigned_by_id": (self.user_client, UserDB, True),
            "created_by_id": (self.user_client, UserDB, True),
            "modify_by_id": (self.user_client, UserDB, False),
            "last_activity_by": (self.user_client, UserDB, False),
        }


def get_company_repository(
    session: AsyncSession = Depends(get_session),
    contact_client: ContactClient = Depends(get_contact_client),
    lead_client: LeadClient = Depends(get_lead_client),
    user_client: UserClient = Depends(get_user_client),
) -> CompanyRepository:
    return CompanyRepository(
        session=session,
        contact_client=contact_client,
        lead_client=lead_client,
        user_client=user_client,
    )
