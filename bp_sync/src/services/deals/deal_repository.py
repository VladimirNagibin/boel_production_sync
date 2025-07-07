from typing import Any, Type

from fastapi import Depends, HTTPException, status
from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base, get_session
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
from schemas.deal_schemas import DealCreate, DealUpdate

from ..leads.lead_services import LeadClient, get_lead_client


class DealRepository:
    def __init__(self, session: AsyncSession, lead_client: LeadClient):
        self.session = session
        self.lead_client = lead_client

    async def create_deal(self, deal_schema: DealCreate) -> DealDB:
        """Создает новую сделку с проверкой на дубликаты"""
        external_id = deal_schema.external_id
        if await self._deal_exists(external_id):
            logger.warning(
                f"Deal creation conflict: ID={external_id} already exists"
            )
            raise self._deal_conflict_exception(external_id)

        try:
            errors = await self._check_related_objects_exist(deal_schema)
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Related objects not found {errors}",
                )
            errors = await self._check_or_create_related_objects(deal_schema)
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Related objects can't created {errors}",
                )
            new_deal = DealDB(**deal_schema.model_dump())
            self.session.add(new_deal)
            await self.session.commit()
            await self.session.refresh(new_deal)
            logger.info(f"Deal created successfully: ID={external_id}")
            return new_deal
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error creating deal ID={external_id}: {str(e)}"
            )
            raise self._deal_conflict_exception(deal_schema.external_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error creating deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create deal in database",
            ) from e

    async def get_deal_by_external_id(self, external_id: int) -> DealDB | None:
        """Возвращает сделку по external_id или None"""
        try:
            stmt = select(DealDB).where(DealDB.external_id == external_id)
            result = await self.session.execute(stmt)
            deal = result.scalar_one_or_none()
            if not deal:
                logger.debug(f"Deal not found: ID={external_id}")
            return deal  # type: ignore
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve deal from database",
            ) from e

    async def update_deal_by_external_id(
        self, deal_schema: DealUpdate
    ) -> DealDB:
        """Обновляет существующую сделку"""
        if not deal_schema.external_id:
            logger.error("Update failed: Missing deal ID")
            raise ValueError("Deal ID is required for update")
        update_data = deal_schema.model_dump(exclude_unset=True)
        external_id = deal_schema.external_id

        if not await self._deal_exists(external_id):
            logger.warning(f"Update failed: Deal ID={external_id} not found")
            raise self._deal_not_found_exception(external_id)

        # Оптимизированный запрос обновления
        stmt = (
            update(DealDB)
            .where(DealDB.external_id == external_id)
            .values(update_data)
            .returning(DealDB)
        )

        try:
            errors = await self._check_related_objects_exist(deal_schema)
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Related objects not found {errors}",
                )
            errors = await self._check_or_create_related_objects(deal_schema)
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Related objects can't created {errors}",
                )
            result = await self.session.execute(stmt)
            updated_deal = result.scalar_one()
            await self.session.commit()
            logger.info(f"Deal updated successfully: ID={external_id}")
            return updated_deal  # type: ignore
        except NoResultFound:
            await self.session.rollback()
            logger.warning(
                f"Update failed: Deal ID={external_id} not found after update"
            )
            raise self._deal_not_found_exception(external_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error updating deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update deal in database",
            ) from e

    async def delete_deal_by_external_id(self, external_id: int) -> bool:
        """Удаляет сделку по external_id, возвращает статус операции"""
        if not await self._deal_exists(external_id):
            logger.warning(f"Delete failed: Deal ID={external_id} not found")
            raise self._deal_not_found_exception(external_id)

        stmt = delete(DealDB).where(DealDB.external_id == external_id)
        try:
            result = await self.session.execute(stmt)
            await self.session.commit()

            if result.rowcount == 0:
                raise self._deal_not_found_exception(external_id)
            logger.info(f"Deal deleted successfully: ID={external_id}")
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error deleting deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete deal from database",
            ) from e

    async def _deal_exists(self, external_id: int) -> bool:
        """Проверяет существование сделки по external_id"""
        try:
            stmt = select(exists().where(DealDB.external_id == external_id))
            result = await self.session.execute(stmt)
            return bool(result.scalar())
        except SQLAlchemyError as e:
            logger.exception(
                "Database error checking deal existence "
                f"ID={external_id}: {str(e)}"
            )
            return False

    def _deal_not_found_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для отсутствующей сделки"""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID: {external_id} not found",
        )

    def _deal_conflict_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для конфликта дубликатов"""
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Deal with ID: {external_id} already exists",
        )

    async def _check_related_objects_exist(
        self, deal_schema: DealCreate | DealUpdate
    ) -> list[str]:
        """Проверяет существование всех связанных объектов в БД"""
        errors: list[str] = []

        # Проверка DealType
        if type_id := deal_schema.type_id:
            if not await self._check_object_exists(
                DealType, external_id=type_id
            ):
                errors.append(f"DealType with type_id={type_id} not found")

        # Проверка DealStage
        if stage_id := deal_schema.stage_id:
            if not await self._check_object_exists(
                DealStage, external_id=stage_id
            ):
                errors.append(f"DealStage with stage_id={stage_id} not found")

        # Проверка Currency
        if currency_id := deal_schema.currency_id:
            if not await self._check_object_exists(
                Currency, external_id=currency_id
            ):
                errors.append(
                    f"Currency with currency_id={currency_id} not found"
                )

        # Проверка Category
        if category_id := deal_schema.category_id:
            if not await self._check_object_exists(
                Category, external_id=category_id
            ):
                errors.append(
                    f"Category with category_id={category_id} not found"
                )

        # Проверка Source
        if source_id := deal_schema.source_id:
            if not await self._check_object_exists(
                Source, external_id=source_id
            ):
                errors.append(f"Source with source_id={source_id} not found")

        # Проверка MainActivity
        if main_activity_id := deal_schema.main_activity_id:
            if not await self._check_object_exists(
                MainActivity, external_id=main_activity_id
            ):
                errors.append(
                    f"MainActivity with id={main_activity_id} not found"
                )

        # Проверка DealType (lead)
        if lead_type_id := deal_schema.lead_type_id:
            if not await self._check_object_exists(
                DealType, external_id=lead_type_id
            ):
                errors.append(
                    f"DealType (lead) with type_id={lead_type_id} not found"
                )

        # Проверка ShippingCompany
        if shipping_company_id := deal_schema.shipping_company_id:
            if not await self._check_object_exists(
                ShippingCompany, external_id=shipping_company_id
            ):
                errors.append(
                    f"ShippingCompany with id={shipping_company_id} not found"
                )

        # Проверка Warehouse
        if warehouse_id := deal_schema.warehouse_id:
            if not await self._check_object_exists(
                Warehouse, external_id=warehouse_id
            ):
                errors.append(f"Warehouse with id={warehouse_id} not found")

        # Проверка CreationSource
        if creation_source_id := deal_schema.creation_source_id:
            if not await self._check_object_exists(
                CreationSource, external_id=creation_source_id
            ):
                errors.append(
                    f"CreationSource with id={creation_source_id} not found"
                )

        # Проверка InvoiceStage
        if invoice_stage_id := deal_schema.invoice_stage_id:
            if not await self._check_object_exists(
                InvoiceStage, external_id=invoice_stage_id
            ):
                errors.append(
                    f"InvoiceStage with id={invoice_stage_id} not found"
                )

        # Проверка DealStage (current)
        if current_stage_id := deal_schema.current_stage_id:
            if not await self._check_object_exists(
                DealStage, external_id=current_stage_id
            ):
                errors.append(
                    f"DealStage (current) with type_id={current_stage_id} "
                    "not found"
                )

        # Проверка Deal (parent)
        if parent_deal_id := deal_schema.parent_deal_id:
            if not await self._check_object_exists(
                DealDB, external_id=parent_deal_id
            ):
                errors.append(
                    f"Deal (parent) with id={parent_deal_id} not found"
                )

        # Проверка DealFailureReason
        if deal_failure_reason_id := deal_schema.deal_failure_reason_id:
            if not await self._check_object_exists(
                DealFailureReason, external_id=deal_failure_reason_id
            ):
                errors.append(
                    f"DealFailureReason with id={deal_failure_reason_id} "
                    "not found"
                )

        return errors

    async def _check_or_create_related_objects(
        self, deal_schema: DealCreate | DealUpdate
    ) -> list[str]:
        """Проверяет существование всех связанных объектов в БД"""
        errors: list[str] = []

        # Проверка Lead
        if lead_id := deal_schema.lead_id:
            try:
                if not await self._check_object_exists(
                    LeadDB, external_id=lead_id
                ):
                    await self.lead_client.create_lead(lead_id)
                else:
                    await self.lead_client.update_lead(lead_id)
            except Exception as e:
                errors.append(
                    f"Lead with id={lead_id:} not found and can't created "
                    f"{str(e)}"
                )

        """
        # Проверка Company
        if not await check_object_exists(
            db, Company, company_id=deal_data["company_id"]
        ):
            errors.append(
                f"Company with company_id={deal_data['company_id']} not found"
            )

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

        # Проверка User для defect_expert_id
        if deal_data.get("defect_expert_id") and not await check_object_exists(
            db, User, user_id=deal_data["defect_expert_id"]
        ):
            errors.append(
                "User (defect expert) with"
                f"id={deal_data['defect_expert_id']} not found"
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


def get_deal_repository(
    session: AsyncSession = Depends(get_session),
    lead_client: LeadClient = Depends(get_lead_client),
) -> DealRepository:
    return DealRepository(session, lead_client)
