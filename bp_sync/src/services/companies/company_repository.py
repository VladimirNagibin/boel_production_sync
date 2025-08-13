from typing import TYPE_CHECKING, Any, Callable, Coroutine, Type

from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base
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
from ..exceptions import CyclicCallException
from ..users.user_services import UserClient

if TYPE_CHECKING:
    from ..contacts.contact_services import ContactClient
    from ..entities.source_services import SourceClient
    from ..leads.lead_services import LeadClient


class CompanyRepository(
    EntityWithCommunicationsRepository[
        CompanyDB, CompanyCreate, CompanyUpdate, int
    ]
):

    model = CompanyDB
    entity_type = EntityType.COMPANY

    def __init__(
        self,
        session: AsyncSession,
        get_contact_client: Callable[[], Coroutine[Any, Any, "ContactClient"]],
        get_lead_client: Callable[[], Coroutine[Any, Any, "LeadClient"]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
        get_source_client: Callable[[], Coroutine[Any, Any, "SourceClient"]],
    ):
        super().__init__(session)
        self.get_contact_client = get_contact_client
        self.get_lead_client = get_lead_client
        self.get_user_client = get_user_client
        self.get_source_client = get_source_client

    async def create_entity(self, data: CompanyCreate) -> CompanyDB:
        """Создает новый контакт с проверкой связанных объектов"""
        await self._check_related_objects(data)
        try:
            await self._create_or_update_related(data)
        except CyclicCallException:
            if not data.external_id:
                logger.error("Update failed: Missing ID")
                raise ValueError("ID is required for update")
            external_id = data.external_id
            data = CompanyCreate.get_default_entity(int(external_id))
        return await self.create(data=data)

    async def update_entity(
        self, data: CompanyCreate | CompanyUpdate
    ) -> CompanyDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("currency_id", Currency, "external_id"),
            ("company_type_id", ContactType, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt3_id"),
            ("deal_failure_reason_id", DealFailureReason, "ext_alt3_id"),
            ("deal_type_id", DealType, "external_id"),
            ("shipping_company_id", ShippingCompany, "external_id"),
            ("industry_id", Industry, "external_id"),
            ("employees_id", Emploees, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        lead_client = await self.get_lead_client()
        contact_client = await self.get_contact_client()
        user_client = await self.get_user_client()
        source_client = await self.get_source_client()
        return {
            "lead_id": (lead_client, LeadDB, False),
            "contact_id": (contact_client, ContactDB, False),
            "assigned_by_id": (user_client, UserDB, True),
            "created_by_id": (user_client, UserDB, True),
            "modify_by_id": (user_client, UserDB, False),
            "last_activity_by": (user_client, UserDB, False),
            "source_id": (source_client, Source, False),
        }
