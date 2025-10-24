from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Sequence, Type

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.logger import logger
from db.postgres import Base
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.deal_models import AdditionalInfo as AddInfoDB
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
from schemas.deal_schemas import (
    AddInfoCreate,
    AddInfoUpdate,
    DealCreate,
    DealUpdate,
)
from schemas.main_activity_schemas import MainActivityCreate

from ..base_repositories.base_repository import BaseRepository
from ..companies.company_services import CompanyClient
from ..contacts.contact_services import ContactClient
from ..entities.source_services import SourceClient
from ..exceptions import ConflictException
from ..invoices.invoice_services import InvoiceClient
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
        get_invoice_client: Callable[[], Coroutine[Any, Any, InvoiceClient]],
    ):
        super().__init__(session)
        self.get_company_client = get_company_client
        self.get_contact_client = get_contact_client
        self.get_lead_client = get_lead_client
        self.get_user_client = get_user_client
        self.get_source_client = get_source_client
        self.get_invoice_client = get_invoice_client

    async def create_entity(self, data: DealCreate) -> DealDB:
        """Создает новую сделку с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data, create=True)
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
        """Асинхронно получает сделки со связанными данными"""
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

    async def get_add_info_by_deal_id(self, deal_id: int) -> AddInfoDB | None:
        """Получить дополнительную информацию по ID сделки"""
        try:
            query = (
                select(AddInfoDB)
                .where(AddInfoDB.deal_id == deal_id)
                .options(selectinload(AddInfoDB.deal))
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при получении дополнительной информации для сделки "
                f"{deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось получить дополнительную информацию для сделки "
                f"{deal_id}"
            ) from e

    async def get_all_add_info(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[AddInfoDB]:
        """Получить всю дополнительную информацию с пагинацией"""
        try:
            query = (
                select(AddInfoDB)
                .offset(skip)
                .limit(limit)
                .options(selectinload(AddInfoDB.deal))
            )
            result = await self.session.execute(query)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при получении списка дополнительной информации: {e}"
            )
            raise RuntimeError(
                "Не удалось получить список дополнительной информации"
            ) from e

    async def create_add_info(self, add_info_data: AddInfoCreate) -> AddInfoDB:
        """Создать новую дополнительную информацию"""
        try:
            # Проверяем, существует ли уже информация для этой сделки
            existing_info = await self.get_add_info_by_deal_id(
                add_info_data.deal_id
            )
            if existing_info:
                raise ConflictException(
                    entity="AdditionalInfo",
                    external_id=add_info_data.deal_id,
                )

            additional_info = AddInfoDB(
                deal_id=add_info_data.deal_id, comment=add_info_data.comment
            )

            self.session.add(additional_info)
            await self.session.commit()
            await self.session.refresh(additional_info)

            # Загружаем связанные данные
            await self.session.refresh(additional_info, ["deal"])

            return additional_info
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка целостности при создании дополнительной информации "
                f"для сделки {add_info_data.deal_id}: {e}"
            )
            raise ValueError(
                "Нарушение целостности данных при создании дополнительной "
                "информации"
            ) from e
        except (ValueError, RuntimeError, ConflictException) as e:
            await self.session.rollback()
            logger.error(
                "Ошибка при создании дополнительной информации для сделки "
                f"{add_info_data.deal_id}: {e}"
            )
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка базы данных при создании дополнительной информации "
                f"для сделки {add_info_data.deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось создать дополнительную информацию из-за ошибки "
                "базы данных"
            ) from e

    async def set_add_info_by_deal_id(
        self, deal_id: int, comment: str
    ) -> bool:
        """Установить дополнительную информацию"""
        try:
            await self.create_add_info(
                AddInfoCreate(deal_id=deal_id, comment=comment)
            )
            return True
        except ConflictException:
            await self.update_add_info(deal_id, AddInfoUpdate(comment=comment))
            return True
        except Exception:
            return False

    async def update_add_info(
        self, deal_id: int, add_info_data: AddInfoUpdate
    ) -> AddInfoDB | None:
        """Обновить дополнительную информацию для сделки"""
        try:
            # Получаем текущие данные
            additional_info = await self.get_add_info_by_deal_id(deal_id)
            if not additional_info:
                return None

            # Обновляем только переданные поля
            update_data = add_info_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(additional_info, field, value)

            await self.session.commit()
            await self.session.refresh(additional_info)

            # Загружаем связанные данные
            await self.session.refresh(additional_info, ["deal"])

            return additional_info
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка целостности при обновлении дополнительной информации "
                f"для сделки {deal_id}: {e}"
            )
            raise ValueError(
                "Нарушение целостности данных при обновлении дополнительной "
                "информации"
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка базы данных при обновлении дополнительной информации "
                f"для сделки {deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось обновить дополнительную информацию из-за ошибки "
                "базы данных"
            ) from e

    async def delete_add_info(self, deal_id: int) -> bool:
        """Удалить дополнительную информацию для сделки"""
        try:
            additional_info = await self.get_add_info_by_deal_id(deal_id)
            if not additional_info:
                return False

            await self.session.delete(additional_info)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(
                "Ошибка базы данных при удалении дополнительной информации "
                f"для сделки {deal_id}: {e}"
            )
            raise RuntimeError(
                "Не удалось удалить дополнительную информацию из-за ошибки "
                "базы данных"
            ) from e

    async def upsert_add_info(
        self, add_info_data: AddInfoCreate
    ) -> AddInfoDB | None:
        """Создать или обновить дополнительную информацию"""
        try:
            # Проверяем, существует ли уже информация для этой сделки
            existing_info = await self.get_add_info_by_deal_id(
                add_info_data.deal_id
            )

            if existing_info:
                # Обновляем существующую запись
                return await self.update_add_info(
                    add_info_data.deal_id,
                    AddInfoUpdate(comment=add_info_data.comment),
                )
            else:
                # Создаем новую запись
                return await self.create_add_info(add_info_data)
        except (ValueError, RuntimeError) as e:
            logger.error(
                "Ошибка при создании/обновлении дополнительной информации для "
                f"сделки {add_info_data.deal_id}: {e}"
            )
            raise

    async def get_external_id_by_sort_order_stage(
        self, sort_order: int
    ) -> str | None:
        """Получить external_id стадии сделки по порядковому номеру"""
        try:
            stmt = select(DealStage.external_id).where(
                DealStage.sort_order == sort_order
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            # Логирование ошибки
            logger.error(
                "Ошибка при получении external_id по sort_order "
                f"{sort_order}: {e}"
            )
            return None

    async def get_sort_order_by_external_id_stage(
        self, external_id: str
    ) -> int | None:
        """Получить порядковый номер стадии сделки по external_id"""
        try:
            stmt = select(DealStage.sort_order).where(
                DealStage.external_id == external_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except Exception as e:
            # Логирование ошибки
            logger.error(
                "Ошибка при получении sort_order по external_id "
                f"{external_id}: {e}"
            )
            return None

    async def get_main_activity_by_entity(
        self, entity_type: EntityType, value: int
    ) -> MainActivityCreate | None:
        # Определяем соответствие между типом сущности и полем в MainActivity
        field_mapping = {
            EntityType.DEAL: MainActivity.external_id,
            EntityType.LEAD: MainActivity.ext_alt_id,
            EntityType.CONTACT: MainActivity.ext_alt2_id,
            EntityType.COMPANY: MainActivity.ext_alt3_id,
            EntityType.INVOICE: MainActivity.ext_alt4_id,
        }

        # Выбираем поле для фильтрации based on entity type
        filter_field = field_mapping.get(entity_type)
        if filter_field is None:
            return None

        # Ищем запись в базе данных
        query = select(MainActivity).where(filter_field == value)

        # Выполняем запрос
        result = await self.session.execute(query)

        # Получаем первый результат
        main_activity = result.scalars().first()

        if main_activity is None:
            return None

        # Преобразуем SQLAlchemy модель в Pydantic модель
        # return MainActivityCreate.model_validate(main_activity)
        return MainActivityCreate(
            internal_id=main_activity.id,
            name=main_activity.name,
            external_id=main_activity.external_id,
            ext_alt_id=main_activity.ext_alt_id,
            ext_alt2_id=main_activity.ext_alt2_id,
            ext_alt3_id=main_activity.ext_alt3_id,
            ext_alt4_id=main_activity.ext_alt4_id,
        )

    async def get_deals_for_checking_processing_status(
        self, current_time: datetime
    ) -> list[DealDB]:
        """Получает сделки для проверки статуса обработки"""
        try:
            first_stages = await self.get_first_four_stages()
            if not first_stages:
                logger.warning("No first stages found")
                return []

            # Получаем сделки для обновления
            stmt = select(DealDB).where(
                and_(
                    DealDB.stage_id.in_(first_stages),
                    DealDB.is_frozen.is_(False),
                    DealDB.moved_date.is_not(None),
                    DealDB.moved_date <= current_time,
                )
            )

            result = await self.session.execute(stmt)
            return result.scalars().all()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сделок: {e}")
            return []

    async def get_first_four_stages(self) -> list[str]:
        """Получает ID первых четырех стадий сделок"""
        try:
            stage_ids: list[str] = []
            for i in range(1, 5):
                external_id = await self.get_external_id_by_sort_order_stage(i)
                if external_id:
                    stage_ids.append(external_id)

            logger.debug(f"Found first four stages: {stage_ids}")
            return stage_ids

        except Exception as e:
            logger.error(f"Error getting first four stages: {e}")
            return []
