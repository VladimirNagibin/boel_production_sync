from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import get_session
from models.bases import EntityType
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
from schemas.lead_schemas import LeadCreate, LeadUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)


class LeadRepository(
    EntityWithCommunicationsRepository[LeadDB, LeadCreate, LeadUpdate]
):

    model = LeadDB
    entity_type = EntityType.LEAD

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_lead(self, lead_schema: LeadCreate) -> LeadDB:
        """Создает новый лид с проверкой связанных объектов"""
        await self._check_related_objects(lead_schema)
        await self._create_or_update_related(lead_schema)
        return await self.create(data=lead_schema)

    async def update_lead(
        self, lead_schema: LeadUpdate | LeadCreate
    ) -> LeadDB:
        """Обновляет существующий лид"""
        await self._check_related_objects(lead_schema)
        await self._create_or_update_related(lead_schema)
        return await self.update(data=lead_schema)

    async def _check_related_objects(
        self, lead_schema: LeadCreate | LeadUpdate
    ) -> None:
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

        if errors:
            logger.exception(f"Related objects not found: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related objects not found: {errors}",
            )

    async def _create_or_update_related(
        self, lead_schema: LeadCreate | LeadUpdate
    ) -> None:
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
        if errors:
            logger.exception(f"Failed to create related objects: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to create related objects: {errors}",
            )


def get_lead_repository(
    session: AsyncSession = Depends(get_session),
) -> LeadRepository:
    return LeadRepository(session)
