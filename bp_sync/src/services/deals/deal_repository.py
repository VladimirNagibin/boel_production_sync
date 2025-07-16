from typing import Type

from fastapi import Depends, HTTPException, status
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

from ..base_repositories.base_repository import BaseRepository
from ..leads.lead_services import LeadClient, get_lead_client


class DealRepository(BaseRepository[DealDB, DealCreate, DealUpdate]):
    """Репозиторий для работы со сделками"""

    model = DealDB

    def __init__(self, session: AsyncSession, lead_client: LeadClient):
        super().__init__(session)
        self.lead_client = lead_client

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

    def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("type_id", DealType, "external_id"),
            ("stage_id", DealStage, "external_id"),
            ("currency_id", Currency, "external_id"),
            ("category_id", Category, "external_id"),
            ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "external_id"),
            ("lead_type_id", DealType, "external_id"),
            ("shipping_company_id", ShippingCompany, "external_id"),
            ("warehouse_id", Warehouse, "external_id"),
            ("creation_source_id", CreationSource, "external_id"),
            ("invoice_stage_id", InvoiceStage, "external_id"),
            ("current_stage_id", DealStage, "external_id"),
            ("parent_deal_id", DealDB, "external_id"),
            ("deal_failure_reason_id", DealFailureReason, "external_id"),
        ]

    async def _create_or_update_related(
        self, deal_schema: DealCreate | DealUpdate
    ) -> None:
        """
        Проверяет существование связанных объектов в БД и создаёт отсутствующие
        """
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
        if errors:
            logger.exception(f"Failed to create related objects: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to create related objects: {errors}",
            )


def get_deal_repository(
    session: AsyncSession = Depends(get_session),
    lead_client: LeadClient = Depends(get_lead_client),
) -> DealRepository:
    return DealRepository(session, lead_client)
