from typing import TYPE_CHECKING, Any, Callable, Coroutine, Type

# from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base  # , get_session
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.lead_models import Lead as LeadDB
from models.references import (
    Currency,
    DealFailureReason,
    DealType,
    LeadStatus,
    MainActivity,
    Source,
)
from models.user_models import User as UserDB
from schemas.lead_schemas import LeadCreate, LeadUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)
from ..users.user_services import UserClient  # , get_user_client

if TYPE_CHECKING:
    from ..companies.company_services import (  # , get_company_client
        CompanyClient,
    )
    from ..contacts.contact_services import (  # , get_contact_client
        ContactClient,
    )
    from ..entities.source_services import SourceClient


class LeadRepository(
    EntityWithCommunicationsRepository[LeadDB, LeadCreate, LeadUpdate, int]
):

    model = LeadDB
    entity_type = EntityType.LEAD

    def __init__(
        self,
        session: AsyncSession,
        # company_client: "CompanyClient",
        # contact_client: "ContactClient",
        # user_client: UserClient,
        get_company_client: Callable[[], Coroutine[Any, Any, "CompanyClient"]],
        get_contact_client: Callable[[], Coroutine[Any, Any, "ContactClient"]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
        get_source_client: Callable[[], Coroutine[Any, Any, "SourceClient"]],
    ):
        super().__init__(session)
        self.get_company_client = get_company_client
        self.get_contact_client = get_contact_client
        self.get_user_client = get_user_client
        self.get_source_client = get_source_client

    async def create_entity(self, data: LeadCreate) -> LeadDB:
        """Создает новый лид с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(self, data: LeadUpdate | LeadCreate) -> LeadDB:
        """Обновляет существующий лид"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("type_id", DealType, "external_id"),
            ("status_id", LeadStatus, "external_id"),
            ("currency_id", Currency, "external_id"),
            # ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt_id"),  # Особое поле
            ("deal_failure_reason_id", DealFailureReason, "ext_alt_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        company_client = await self.get_company_client()
        contact_client = await self.get_contact_client()
        user_client = await self.get_user_client()
        source_client = await self.get_source_client()
        return {
            "company_id": (company_client, CompanyDB, False),
            "contact_id": (contact_client, ContactDB, False),
            "assigned_by_id": (user_client, UserDB, True),
            "created_by_id": (user_client, UserDB, True),
            "modify_by_id": (user_client, UserDB, False),
            "moved_by_id": (user_client, UserDB, False),
            "last_activity_by": (user_client, UserDB, False),
            "source_id": (source_client, Source, False),
        }


# def get_lead_repository(
#    session: AsyncSession = Depends(get_session),
#    # company_client: "CompanyClient" = Depends(get_company_client),
#    # contact_client: "ContactClient" = Depends(get_contact_client),
#    user_client: UserClient = Depends(get_user_client),
# ) -> LeadRepository:
#    from ..companies.company_services import get_company_client
#    from ..contacts.contact_services import get_contact_client

#    return LeadRepository(
#        session=session,
#        company_client=Depends(get_company_client),
#        contact_client=Depends(get_contact_client),
#        user_client=user_client,
#    )
