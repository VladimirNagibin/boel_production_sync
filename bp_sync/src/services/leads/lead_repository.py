from typing import Any, Type

from fastapi import Depends, HTTPException, status
from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base, get_session
from models.bases import COMMUNICATION_TYPES, CommunicationType, EntityType
from models.communications import (
    CommunicationChannel,
    CommunicationChannelType,
)
from models.entities import Company
from models.lead_models import Lead as LeadDB
from models.references import (
    Currency,
    DealFailureReason,
    DealType,
    LeadStatus,
    MainActivity,
    Source,
)
from schemas.lead_schemas import CommunicationChannel as CommSchema
from schemas.lead_schemas import (
    LeadCreate,
    LeadUpdate,
)


class LeadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_lead(self, lead_schema: LeadCreate) -> LeadDB:
        """Создает новый лид с проверкой на дубликаты"""
        external_id = lead_schema.external_id
        if await self._lead_exists(external_id):
            logger.warning(
                f"Lead creation conflict: ID={external_id} already exists"
            )
            raise self._lead_conflict_exception(external_id)

        try:
            lead_dict = lead_schema.model_dump(
                exclude=set(COMMUNICATION_TYPES.keys())
            )
            new_lead = LeadDB(**lead_dict)
            self.session.add(new_lead)
            await self.session.flush()  # Получаем ID лида

            for field, comm_type in COMMUNICATION_TYPES.items():
                if communications := getattr(lead_schema, field):
                    for comm_schema in communications:
                        await self._create_communication_channel(
                            lead=new_lead,
                            comm_schema=comm_schema,
                            comm_type=comm_type,
                        )
            await self.session.commit()
            await self.session.refresh(new_lead)
            logger.info(f"Lead created successfully: ID={external_id}")
            return new_lead
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error creating deal ID={external_id}: {str(e)}"
            )
            raise self._lead_conflict_exception(lead_schema.external_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error creating lead ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lead in database",
            ) from e

    async def get_lead_by_external_id(self, external_id: int) -> LeadDB | None:
        """Возвращает лид по external_id или None"""
        try:
            stmt = select(LeadDB).where(LeadDB.external_id == external_id)
            result = await self.session.execute(stmt)
            lead = result.scalar_one_or_none()
            if not lead:
                logger.debug(f"Lead not found: ID={external_id}")
            return lead  # type: ignore
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching lead ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve lead from database",
            ) from e

    async def update_lead_by_external_id(
        self, lead_schema: LeadUpdate | LeadCreate
    ) -> LeadDB:
        """Обновляет существующий лид"""
        if not lead_schema.external_id:
            logger.error("Update failed: Missing lead ID")
            raise ValueError("Lead ID is required for update")
        update_data = lead_schema.model_dump(
            exclude_unset=True, exclude=set(COMMUNICATION_TYPES.keys())
        )
        external_id = lead_schema.external_id

        if not await self._lead_exists(external_id):
            logger.warning(f"Update failed: Lead ID={external_id} not found")
            raise self._lead_not_found_exception(external_id)

        # Оптимизированный запрос обновления
        stmt = (
            update(LeadDB)
            .where(LeadDB.external_id == external_id)
            .values(update_data)
            .returning(LeadDB)
        )

        try:
            result = await self.session.execute(stmt)
            updated_lead = result.scalar_one()
            for field, comm_type in COMMUNICATION_TYPES.items():
                if hasattr(lead_schema, field):
                    new_comms = getattr(lead_schema, field)
                    await self._update_communications(
                        lead=updated_lead,
                        comm_type=comm_type,
                        new_comms=new_comms,
                    )
            await self.session.commit()
            await self.session.refresh(updated_lead)
            logger.info(f"Lead updated successfully: ID={external_id}")
            return updated_lead  # type: ignore
        except NoResultFound:
            await self.session.rollback()
            logger.warning(
                f"Update failed: Lead ID={external_id} not found after update"
            )
            raise self._lead_not_found_exception(external_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error updating lead ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update lead in database",
            ) from e

    async def delete_lead_by_external_id(self, external_id: int) -> bool:
        """Удаляет лид по external_id, возвращает статус операции"""
        if not await self._lead_exists(external_id):
            logger.warning(f"Delete failed: Lead ID={external_id} not found")
            raise self._lead_not_found_exception(external_id)

        try:
            # 1. Удаляем все коммуникации лида
            await self._delete_all_communications(
                entity_type=EntityType.LEAD.value, entity_id=external_id
            )

            # 2. Удаляем сам лид
            stmt = delete(LeadDB).where(LeadDB.external_id == external_id)
            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                raise self._lead_not_found_exception(external_id)
            await self.session.commit()

            logger.info(f"Lead deleted successfully: ID={external_id}")
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error deleting Lead ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete lead from database",
            ) from e

    async def _lead_exists(self, external_id: int) -> bool:
        """Проверяет существование лида по external_id"""
        try:
            stmt = select(exists().where(LeadDB.external_id == external_id))
            result = await self.session.execute(stmt)
            return bool(result.scalar())
        except SQLAlchemyError as e:
            logger.exception(
                "Database error checking deal existence "
                f"ID={external_id}: {str(e)}"
            )
            return False

    def _lead_not_found_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для отсутствующго лида"""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID: {external_id} not found",
        )

    def _lead_conflict_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для конфликта дубликатов"""
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lead with ID: {external_id} already exists",
        )

    async def _create_communication_channel(
        self,
        lead: LeadDB,
        comm_schema: CommSchema,
        comm_type: CommunicationType,
    ) -> bool:
        """Создаёт коммуникации"""
        try:
            # 1. Поиск типа канала
            stmt = select(CommunicationChannelType).where(
                CommunicationChannelType.type_id == comm_type.value,
                CommunicationChannelType.value_type == comm_schema.value_type,
            )
            result = await self.session.execute(stmt)
            channel_type = result.scalars().first()

            # 2. Создание типа канала, если не найден
            if not channel_type:
                logger.info(
                    "Creating new channel type: "
                    f"{comm_type.value}/{comm_schema.value_type} "
                    f"for lead ID: {lead.external_id}"
                )
                channel_type = CommunicationChannelType(
                    type_id=comm_type.value,
                    value_type=comm_schema.value_type,
                    description=f"Automatically created for {comm_type.value}",
                )
                self.session.add(channel_type)
                await self.session.flush()  # Частичное сохранение для ID
                await self.session.refresh(channel_type)

                logger.debug(
                    f"Created channel type ID: {channel_type.id} "
                    f"({comm_type.value}/{comm_schema.value_type})"
                )

            # 3. Создание канала связи
            channel = CommunicationChannel(
                external_id=comm_schema.external_id,  # Используем ID из схемы
                entity_type=EntityType.LEAD.value,  # Преобразуем enum в знач
                entity_id=lead.external_id,
                channel_type_id=channel_type.id,
                value=comm_schema.value,
            )

            self.session.add(channel)
            await self.session.flush()  # Частичн сохран без полного коммита
            logger.debug(
                f"Created communication channel for lead {lead.external_id}: "
                f"{comm_type.value} - {comm_schema.value}"
            )
            return True

        except SQLAlchemyError as e:
            logger.error(
                "Database error creating communication channel for "
                f"lead {lead.external_id}: Type: {comm_type.value}, "
                f"Value: {comm_schema.value} - {str(e)}"
            )
            # Откатываем изменения в текущей транзакции
            await self.session.rollback()
            return False

        except Exception as e:
            logger.exception(
                f"Unexpected error {str(e)} creating communication channel "
                f"for lead {lead.external_id}: Type: {comm_type.value}, "
                f"Value: {comm_schema.value}"
            )
            await self.session.rollback()
            return False

    async def _update_communications(
        self,
        lead: LeadDB,
        comm_type: CommunicationType,
        new_comms: list[CommSchema] | None,
    ) -> None:
        """
        Обновляет коммуникации лида:
        - Если new_comms is None - пропускаем обновление
        - Если пустой список - удаляем все коммуникации этого типа
        - Если список с элементами - заменяем существующие
        """
        if new_comms is None:
            return  # Пропускаем обновление

        # Удаляем все существующие коммуникации этого типа
        await self._delete_communications(
            entity_type=EntityType.LEAD.value,
            entity_id=lead.external_id,
            comm_type=comm_type,
        )

        # Добавляем новые коммуникации
        if new_comms:
            for comm_schema in new_comms:
                await self._create_communication_channel(
                    lead=lead, comm_schema=comm_schema, comm_type=comm_type
                )

    async def _delete_communications(
        self,
        entity_type: str,
        entity_id: int,
        comm_type: CommunicationType | None = None,
    ) -> None:
        """Удаляет коммуникации сущности, опционально фильтруя по типу"""
        try:
            # Базовый запрос на удаление
            delete_stmt = delete(CommunicationChannel).where(
                CommunicationChannel.entity_type == entity_type,
                CommunicationChannel.entity_id == entity_id,
            )

            # Если указан тип, добавляем фильтр по типу канала
            if comm_type:
                # Подзапрос для ID типов каналов
                subquery = (
                    select(CommunicationChannelType.id)
                    .where(CommunicationChannelType.type_id == comm_type.value)
                    .scalar_subquery()
                )

                delete_stmt = delete_stmt.where(
                    CommunicationChannel.channel_type_id.in_(subquery)
                )

            await self.session.execute(delete_stmt)
            logger.debug(
                f"Deleted communications for {entity_type} ID={entity_id}, "
                f"type: {comm_type.value if comm_type else 'all'}"
            )
        except SQLAlchemyError as e:
            logger.error(
                f"Error deleting communications for {entity_type} "
                f"ID={entity_id}: {str(e)}"
            )
            raise

    async def _delete_all_communications(
        self, entity_type: str, entity_id: int
    ) -> None:
        """Удаляет все коммуникации сущности"""
        await self._delete_communications(
            entity_type=entity_type, entity_id=entity_id
        )

    async def _check_related_objects_exist(
        self, lead_schema: LeadCreate | LeadUpdate
    ) -> list[str]:
        """Проверяет существование всех связанных объектов в БД"""
        errors: list[str] = []

        # Проверка DealType
        if type_id := lead_schema.type_id:
            if not await self._check_object_exists(
                DealType, external_id=type_id
            ):
                errors.append(f"DealType with type_id={type_id} not found")

        # Проверка DealStage
        if status_id := lead_schema.status_id:
            if not await self._check_object_exists(
                LeadStatus, external_id=status_id
            ):
                errors.append(
                    f"LeadStatus with status_id={status_id} not found"
                )

        # Проверка Currency
        if currency_id := lead_schema.currency_id:
            if not await self._check_object_exists(
                Currency, external_id=currency_id
            ):
                errors.append(
                    f"Currency with currency_id={currency_id} not found"
                )

        # Проверка Source
        if source_id := lead_schema.source_id:
            if not await self._check_object_exists(
                Source, external_id=source_id
            ):
                errors.append(f"Source with source_id={source_id} not found")

        # Проверка MainActivity
        if main_activity_id := lead_schema.main_activity_id:
            if not await self._check_object_exists(
                MainActivity, ext_alt_id=main_activity_id
            ):
                errors.append(
                    f"MainActivity with id={main_activity_id} not found"
                )

        # Проверка DealFailureReason
        if deal_failure_reason_id := lead_schema.deal_failure_reason_id:
            if not await self._check_object_exists(
                DealFailureReason, ext_alt_id=deal_failure_reason_id
            ):
                errors.append(
                    f"DealFailureReason with id={deal_failure_reason_id} "
                    "not found"
                )

        return errors

    async def _check_or_create_related_objects(
        self, lead_schema: LeadCreate | LeadUpdate
    ) -> list[str]:
        """
        Проверяет существование всех связанных объектов в БД и
        создаёт при отсутствии
        """
        errors: list[str] = []

        # Проверка company
        if company_id := lead_schema.company_id:
            if not await self._check_object_exists(
                Company, external_id=company_id
            ):
                errors.append(f"Company with id={company_id:} not found")

        """
        # Проверка Contact
        if not await check_object_exists(
            db, Company, company_id=deal_data["company_id"]
        ):
            errors.append(
                f"Company with company_id={deal_data['company_id']} not found"
            )

        # Проверка User для assigned_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["assigned_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['assigned_by_id']} not found"
            )

        # Проверка User для created_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["created_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['created_by_id']} not found"
            )

        # Проверка User для modify_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["modify_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['modify_by_id']} not found"
            )

        # Проверка User для moved_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["moved_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['moved_by_id']} not found"
            )

        # Проверка User для last_activity_by
        if not await check_object_exists(
            db, User, user_id=deal_data["last_activity_by"]
        ):
            errors.append(
                f"User with user_id={deal_data['last_activity_by']} not found"
            )
        """
        return errors

    async def _check_object_exists(
        self, model: Type[Base], **filters: Any
    ) -> bool:
        """Проверяет существование объекта в БД по заданным фильтрам"""
        stmt = select(model).filter_by(**filters).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


def get_lead_repository(
    session: AsyncSession = Depends(get_session),
) -> LeadRepository:
    return LeadRepository(session)
