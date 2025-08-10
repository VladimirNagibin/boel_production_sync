from typing import Any, Callable, Coroutine, Type

# from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base  # , get_session
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.deal_models import Deal as DealDB
from models.lead_models import Lead as LeadDB
from models.references import (
    Category,
    CreationSource,
    Currency,
    DealFailureReason,
    DealStage,
    DealType,
    InvoiceStage,
    MainActivity,
    ShippingCompany,
    Source,
    Warehouse,
)
from models.user_models import User as UserDB
from schemas.deal_schemas import DealCreate, DealUpdate

from ..base_repositories.base_repository import BaseRepository
from ..companies.company_services import CompanyClient  # , get_company_client
from ..contacts.contact_services import ContactClient  # , get_contact_client
from ..entities.source_services import SourceClient
from ..leads.lead_services import LeadClient  # , get_lead_client
from ..users.user_services import UserClient  # , get_user_client


class DealRepository(BaseRepository[DealDB, DealCreate, DealUpdate, int]):
    """Репозиторий для работы со сделками"""

    model = DealDB
    entity_type = EntityType.DEAL

    def __init__(
        self,
        session: AsyncSession,
        # company_client: CompanyClient,
        # contact_client: ContactClient,
        # lead_client: LeadClient,
        # user_client: UserClient,
        get_company_client: Callable[[], Coroutine[Any, Any, CompanyClient]],
        get_contact_client: Callable[[], Coroutine[Any, Any, ContactClient]],
        get_lead_client: Callable[[], Coroutine[Any, Any, LeadClient]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
        get_source_client: Callable[[], Coroutine[Any, Any, SourceClient]],
    ):
        super().__init__(session)
        self.get_company_client = get_company_client
        self.get_contact_client = get_contact_client
        self.get_lead_client = get_lead_client
        self.get_user_client = get_user_client
        self.get_source_client = get_source_client

    async def create_entity(self, data: DealCreate) -> DealDB:
        """Создает новую сделку с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(self, data: DealUpdate | DealCreate) -> DealDB:
        """Обновляет существующую сделку"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("type_id", DealType, "external_id"),
            ("stage_id", DealStage, "external_id"),
            ("currency_id", Currency, "external_id"),
            ("category_id", Category, "external_id"),
            # ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "external_id"),
            ("lead_type_id", DealType, "external_id"),
            ("shipping_company_id", ShippingCompany, "ext_alt_id"),
            ("warehouse_id", Warehouse, "external_id"),
            ("creation_source_id", CreationSource, "external_id"),
            ("invoice_stage_id", InvoiceStage, "external_id"),
            ("current_stage_id", DealStage, "external_id"),
            # ("parent_deal_id", DealDB, "external_id"),
            ("deal_failure_reason_id", DealFailureReason, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        company_client = await self.get_company_client()
        contact_client = await self.get_contact_client()
        user_client = await self.get_user_client()
        lead_client = await self.get_lead_client()
        source_client = await self.get_source_client()
        return {
            "lead_id": (lead_client, LeadDB, False),
            "company_id": (company_client, CompanyDB, False),
            "contact_id": (contact_client, ContactDB, False),
            "assigned_by_id": (user_client, UserDB, True),
            "created_by_id": (user_client, UserDB, True),
            "modify_by_id": (user_client, UserDB, False),
            "moved_by_id": (user_client, UserDB, False),
            "last_activity_by": (user_client, UserDB, False),
            "defect_expert_id": (user_client, UserDB, False),
            "source_id": (source_client, Source, False),
        }

    """
    async def _create_or_update_related(
        self, deal_schema: DealCreate | DealUpdate
    ) -> None:
        "
        Проверяет существование связанных объектов в БД и создаёт отсутствующие
        "
        errors: list[str] = []

        # Проверка Lead
        if lead_id := deal_schema.lead_id:
            try:
                if not await self._check_object_exists(
                    LeadDB, external_id=lead_id
                ):
                    await self.lead_client.import_from_bitrix(lead_id)
                else:
                    await self.lead_client.refresh_from_bitrix(lead_id)
            except Exception as e:
                errors.append(
                    f"Lead with id={lead_id:} not found and can't created "
                    f"{str(e)}"
                )

        # Проверка Company
        if company_id := deal_schema.company_id:
            try:
                if not await self._check_object_exists(
                    CompanyDB, external_id=company_id
                ):
                    await self.company_client.import_from_bitrix(company_id)
                else:
                    await self.company_client.refresh_from_bitrix(company_id)
            except Exception as e:
                errors.append(
                    f"Company with id={company_id:} not found and "
                    f"can't created {str(e)}"
                )

        # Проверка Contact
        if contact_id := deal_schema.contact_id:
            try:
                if not await self._check_object_exists(
                    ContactDB, external_id=contact_id
                ):
                    await self.contact_client.import_from_bitrix(contact_id)
                else:
                    await self.contact_client.refresh_from_bitrix(contact_id)
            except Exception as e:
                errors.append(
                    f"Contact with id={contact_id:} not found and "
                    f"can't created {str(e)}"
                )

        # Проверка User для assigned_by_id
        if user_id := deal_schema.assigned_by_id:
            try:
                if not await self._check_object_exists(
                    UserDB, external_id=user_id
                ):
                    await self.user_client.import_from_bitrix(user_id)
                else:
                    await self.user_client.refresh_from_bitrix(user_id)
            except Exception as e:
                errors.append(
                    f"User with id={user_id:} not found and "
                    f"can't created {str(e)}"
                )

        # Проверка User для created_by_id
        if user_id := deal_schema.created_by_id:
            try:
                if not await self._check_object_exists(
                    UserDB, external_id=user_id
                ):
                    await self.user_client.import_from_bitrix(user_id)
                else:
                    await self.user_client.refresh_from_bitrix(user_id)
            except Exception as e:
                errors.append(
                    f"User with id={user_id:} not found and "
                    f"can't created {str(e)}"
                )

        # Проверка User для modify_by_id
        if user_id := deal_schema.modify_by_id:
            try:
                if not await self._check_object_exists(
                    UserDB, external_id=user_id
                ):
                    await self.user_client.import_from_bitrix(user_id)
                else:
                    await self.user_client.refresh_from_bitrix(user_id)
            except Exception as e:
                errors.append(
                    f"User with id={user_id:} not found and "
                    f"can't created {str(e)}"
                )


        # Проверка User для moved_by_id
        if user_id := deal_schema.moved_by_id:
            try:
                if not await self._check_object_exists(
                    UserDB, external_id=user_id
                ):
                    await self.user_client.import_from_bitrix(user_id)
                else:
                    await self.user_client.refresh_from_bitrix(user_id)
            except Exception as e:
                errors.append(
                    f"User with id={user_id:} not found and "
                    f"can't created {str(e)}"
                )

        # Проверка User для last_activity_by
        if user_id := deal_schema.last_activity_by:
            try:
                if not await self._check_object_exists(
                    UserDB, external_id=user_id
                ):
                    await self.user_client.import_from_bitrix(user_id)
                else:
                    await self.user_client.refresh_from_bitrix(user_id)
            except Exception as e:
                errors.append(
                    f"User with id={user_id:} not found and "
                    f"can't created {str(e)}"
                )

        # Проверка User для defect_expert_id
        if user_id := deal_schema.defect_expert_id:
            try:
                if not await self._check_object_exists(
                    UserDB, external_id=user_id
                ):
                    await self.user_client.import_from_bitrix(user_id)
                else:
                    await self.user_client.refresh_from_bitrix(user_id)
            except Exception as e:
                errors.append(
                    f"User with id={user_id:} not found and "
                    f"can't created {str(e)}"
                )

        if errors:
            logger.exception(f"Failed to create related objects: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to create related objects: {errors}",
            )
        """


# def get_deal_repository(
#    session: AsyncSession = Depends(get_session),
#    company_client: CompanyClient = Depends(get_company_client),
#    contact_client: ContactClient = Depends(get_contact_client),
#    lead_client: LeadClient = Depends(get_lead_client),
#    user_client: UserClient = Depends(get_user_client),
# ) -> DealRepository:
#    return DealRepository(
#        session=session,
#        company_client=company_client,
#        contact_client=contact_client,
#        lead_client=lead_client,
#        user_client=user_client,
#    )
