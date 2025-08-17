from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Type

from pytz import UTC  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
        result = await self.session.execute(
            select(DealDB)
            .where(
                DealDB.date_create >= start_date,
                DealDB.date_create <= end_date_plus_one,
            )
            .options(
                # Загрузка отношений для Deal
                selectinload(DealDB.assigned_user),
                selectinload(DealDB.created_user),
                selectinload(DealDB.type),
                selectinload(DealDB.stage),
                selectinload(DealDB.source),
                selectinload(DealDB.creation_source),
                selectinload(DealDB.timeline_comments),
                selectinload(DealDB.timeline_comments).selectinload(
                    TimelineComment.author
                ),
                # Загрузка отношений для Lead
                selectinload(DealDB.lead).selectinload(LeadDB.assigned_user),
                selectinload(DealDB.lead).selectinload(LeadDB.created_user),
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
                selectinload(DealDB.invoices).selectinload(InvoiceDB.billings),
                selectinload(DealDB.lead),
                selectinload(DealDB.invoices).selectinload(
                    InvoiceDB.delivery_notes
                ),
                selectinload(DealDB.invoices).selectinload(InvoiceDB.company),
                selectinload(DealDB.invoices).selectinload(InvoiceDB.billings),
            )
        )
        return result.scalars().all()

    def get_name(self, value: Any) -> str:
        """Безопасное получение имени из объекта"""
        if value is None:
            return ""

        # Для пользователей
        if hasattr(value, "full_name") and value.full_name:
            return str(value.full_name)
        if hasattr(value, "name") and value.name:
            return str(value.name)
        if hasattr(value, "title") and value.title:
            return str(value.title)

        # Для перечислений
        if isinstance(value, Enum):
            return value.name

        return ""

    def build_data_row(self, deal: DealDB) -> dict[str, Any]:
        """Строит строку данных для экспорта"""
        row: dict[str, Any] = {
            "ИД сделки": deal.external_id,
            "Дата сделки": deal.date_create,
            "Название сделки": deal.title,
            "Ответственный по сделке": self.get_name(deal.assigned_user),
            "Создатель сделки": self.get_name(deal.created_user),
            "Сумма сделки": deal.opportunity,
            "Тип созд. сделки": self.get_name(deal.creation_source),
            "Тип создания новый (авто/ручной)": "",
            "Источник сделки": self.get_name(deal.source),
            "Источник новый": "",
            "Тип сделки": self.get_name(deal.type),
            "Тип новый": "",
            "Стадия сделки": self.get_name(deal.stage),
            "Вн ном сделки": deal.origin_id,
            "ИД сайта Calltouch": deal.calltouch_site_id,
            # "deal_calltouch_call_id": deal.calltouch_call_id,
            # "deal_calltouch_request_id": deal.calltouch_request_id,
            "ИД клиента Яндекс": deal.yaclientid,
        }

        # Данные лида
        if deal.lead:
            row.update(
                {
                    "ИД лида": deal.lead.external_id,
                    "Дата лида": deal.lead.date_create,
                    "Название лида": deal.lead.title,
                    "Ответственный по лиду": self.get_name(
                        deal.lead.assigned_user
                    ),
                    "Создатель лида": self.get_name(deal.lead.created_user),
                    "Источник лида": self.get_name(deal.lead.source),
                    "Тип лида": self.get_name(deal.lead.type),
                    "Стадия лида": self.get_name(deal.lead.status),
                    "ИД сайта Calltouch лид": deal.lead.calltouch_site_id,
                    "ИД клиента Яндекс лид": deal.lead.yaclientid,
                }
            )
        # Данные комментариев
        if deal.timeline_comments:
            comments: list[str] = []
            authors: set[str] = set()
            date_comm: datetime | None = None
            for comm in deal.timeline_comments:
                if comm.comment_entity:
                    comments.append(comm.comment_entity)
                author_name = self.get_name(comm.author)
                if author_name:
                    authors.add(author_name)
                if date_comm is None:
                    date_comm = comm.created
            row.update(
                {
                    "Комментарии из ленты": "; ".join(comments),
                    "Автор комментария": (
                        ", ".join(authors) if authors else ""
                    ),
                    "Дата комментария": date_comm,
                }
            )

        # Данные счетов
        if deal.invoices:
            invoice = deal.invoices[0]
            print(invoice)
            row.update(
                {
                    "ИД счета": invoice.external_id,
                    "Дата счета": invoice.date_create,
                    "Название счета": invoice.title,
                    "Ответственный по счету": self.get_name(
                        invoice.assigned_user
                    ),
                    "Номер счета": invoice.account_number,
                    "Компания": self.get_name(invoice.company),
                    "Выгружен в 1С": invoice.is_loaded,
                    "Сумма счета": invoice.opportunity,
                    "Стадия счета": self.get_name(invoice.invoice_stage),
                    "Оплачено по счету": sum(
                        b.amount for b in invoice.billings
                    ),
                    "Статус оплаты": (
                        "Оплачен"
                        if abs(
                            sum(b.amount for b in invoice.billings)
                            - invoice.opportunity
                        )
                        < 0.01
                        else "Частично" if any(invoice.billings) else "-"
                    ),
                }
            )

            # Данные накладных
            if invoice.delivery_notes:
                names: list[str] = []
                opportunity = 0.0
                assigned_users: set[str] = set()
                date_delivery_note = None
                for note in invoice.delivery_notes:
                    names.append(note.name)
                    opportunity += note.opportunity
                    user_name = self.get_name(note.assigned_user)
                    if user_name:
                        assigned_users.add(user_name)
                    if date_delivery_note is None:
                        date_delivery_note = note.date_delivery_note
                row.update(
                    {
                        "Накладная 1С": ", ".join(names),
                        "Сумма накладной": opportunity,
                        "Ответственный по накладной": (
                            ", ".join(assigned_users) if assigned_users else ""
                        ),
                        "Дата накладной": date_delivery_note,
                    }
                )
            else:
                ...
                # yield invoice_row
        else:
            ...
        return row

    @staticmethod
    def convert_to_naive_datetime(value: Any) -> Any:
        """
        Преобразует datetime с временной зоной в наивный datetime
        (без временной зоны)
        """
        if isinstance(value, datetime) and value.tzinfo is not None:
            # Конвертируем в UTC и удаляем информацию о временной зоне
            return value.astimezone(UTC).replace(tzinfo=None)
        return value
