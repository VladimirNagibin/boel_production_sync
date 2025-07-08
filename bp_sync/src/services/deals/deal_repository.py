from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import get_session
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

    async def create_deal(self, deal_schema: DealCreate) -> DealDB:
        """Создает новую сделку с проверкой связанных объектов"""
        await self._check_related_objects(deal_schema)
        await self._create_or_update_related(deal_schema)
        return await self.create(data=deal_schema)

    async def update_deal(self, deal_schema: DealUpdate) -> DealDB:
        """Обновляет существующую сделку"""
        await self._check_related_objects(deal_schema)
        await self._create_or_update_related(deal_schema)
        return await self.update(data=deal_schema)

    async def _check_related_objects(
        self, deal_schema: DealCreate | DealUpdate
    ) -> None:
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

        if errors:
            logger.exception(f"Related objects not found: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related objects not found: {errors}",
            )

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
