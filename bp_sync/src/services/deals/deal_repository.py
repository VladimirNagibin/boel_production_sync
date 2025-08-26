from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.logger import logger
from db.postgres import Base
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.deal_models import Deal as DealDB
from models.delivery_note_models import DeliveryNote
from models.invoice_models import Invoice as InvoiceDB
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
from models.timeline_comment_models import TimelineComment
from models.user_models import User as UserDB
from schemas.deal_schemas import DealCreate, DealUpdate

from ..base_repositories.base_repository import BaseRepository
from ..companies.company_services import CompanyClient
from ..contacts.contact_services import ContactClient
from ..entities.source_services import SourceClient
from ..leads.lead_services import LeadClient
from ..users.user_services import UserClient


class DealRepository(BaseRepository[DealDB, DealCreate, DealUpdate, int]):
    """Репозиторий для работы со сделками"""

    model = DealDB
    entity_type = EntityType.DEAL

    def __init__(
        self,
        session: AsyncSession,
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

    async def fetch_deals(
        self, start_date: datetime, end_date: datetime
    ) -> Any:
        """Асинхронно получает сделки с связанными данными"""
        # Рассчитываем конец периода как начало следующего дня
        end_date_plus_one = end_date + timedelta(days=1)
        try:
            result = await self.session.execute(
                select(DealDB)
                .where(
                    DealDB.date_create >= start_date,
                    DealDB.date_create <= end_date_plus_one,
                )
                .options(
                    # Загрузка отношений для Deal
                    selectinload(DealDB.assigned_user),
                    selectinload(DealDB.assigned_user).selectinload(
                        UserDB.department
                    ),
                    selectinload(DealDB.created_user),
                    selectinload(DealDB.type),
                    selectinload(DealDB.stage),
                    selectinload(DealDB.source),
                    selectinload(DealDB.creation_source),
                    selectinload(DealDB.timeline_comments),
                    selectinload(DealDB.timeline_comments).selectinload(
                        TimelineComment.author
                    ),
                    selectinload(DealDB.company),
                    # Загрузка отношений для Lead
                    selectinload(DealDB.lead).selectinload(
                        LeadDB.assigned_user
                    ),
                    selectinload(DealDB.lead).selectinload(
                        LeadDB.created_user
                    ),
                    selectinload(DealDB.lead).selectinload(LeadDB.type),
                    selectinload(DealDB.lead).selectinload(LeadDB.status),
                    selectinload(DealDB.lead).selectinload(LeadDB.source),
                    # Загрузка отношений для Invoice
                    selectinload(DealDB.invoices).selectinload(
                        InvoiceDB.assigned_user
                    ),
                    selectinload(DealDB.invoices).selectinload(
                        InvoiceDB.created_user
                    ),
                    selectinload(DealDB.invoices).selectinload(
                        InvoiceDB.invoice_stage
                    ),
                    # Загрузка отношений для DeliveryNote
                    selectinload(DealDB.invoices)
                    .selectinload(InvoiceDB.delivery_notes)
                    .selectinload(DeliveryNote.assigned_user),
                    selectinload(DealDB.invoices).selectinload(
                        InvoiceDB.billings
                    ),
                    selectinload(DealDB.lead),
                    selectinload(DealDB.invoices).selectinload(
                        InvoiceDB.delivery_notes
                    ),
                    selectinload(DealDB.invoices).selectinload(
                        InvoiceDB.company
                    ),
                    selectinload(DealDB.invoices).selectinload(
                        InvoiceDB.billings
                    ),
                )
            )
            return result.scalars().all()
        except Exception as e:
            # Логируем ошибку и пробрасываем дальше
            logger.error(f"Error fetching deals: {str(e)}")
            raise
