from datetime import datetime
from typing import Any

from fastapi import HTTPException

from core.logger import logger
from models.deal_models import Deal as DealDB
from schemas.company_schemas import CompanyCreate
from schemas.deal_schemas import DealCreate, DealUpdate
from schemas.lead_schemas import LeadCreate

from ..base_services.base_service import BaseEntityClient
from ..timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from .deal_bitrix_services import DealBitrixClient
from .deal_repository import DealRepository
from .enums import CreationSourceEnum, DealSourceEnum, DealTypeEnum
from .handling_helpers import WEBSITE_CREATOR, identify_source
from .report_helpers import (
    create_dataframe,
    create_excel_file,
    process_deal_row_report,
)


class DealClient(BaseEntityClient[DealDB, DealRepository, DealBitrixClient]):
    """Клиент для работы со сделками"""

    def __init__(
        self,
        deal_bitrix_client: DealBitrixClient,
        deal_repo: DealRepository,
        timeline_comments_bitrix_client: TimeLineCommentBitrixClient,
    ):
        self._bitrix_client = deal_bitrix_client
        self._repo = deal_repo
        self.timeline_comments_bitrix_client = timeline_comments_bitrix_client

    @property
    def entity_name(self) -> str:
        return "deal"

    @property
    def bitrix_client(self) -> DealBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> DealRepository:
        return self._repo

    # deal report for the period
    async def _prepare_data_report(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Подготавливает данные для экспорта"""
        deals = await self.repo.fetch_deals(start_date, end_date)
        if not deals:
            logger.warning(f"No deals found for {start_date}-{end_date}")
            raise HTTPException(
                status_code=404, detail="No deals found in specified period"
            )

        return [await process_deal_row_report(deal) for deal in deals]

    async def export_deals_to_excel(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Основной метод экспорта сделок в Excel"""
        try:
            logger.info(
                f"Exporting deals to excel from {start_date} to {end_date}"
            )
            data = await self._prepare_data_report(start_date, end_date)
            df = await create_dataframe(data)
            return await create_excel_file(df)
        except Exception as e:
            logger.error(f"Export failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Export error: {str(e)}"
            ) from e

    # handling deal
    async def handler_deal(self, external_id: int) -> None:
        """Обработчик сделки"""
        try:
            deal_update = DealUpdate()
            deal_b24, deal_db, changes = await self.get_changes_b24_db(
                external_id
            )
            logger.debug(f"Changes detected for deal {external_id}: {changes}")
            needs_update = await self._check_source(
                deal_b24, deal_db, deal_update
            )
            if deal_db is None:  # not in database
                needs_update = (
                    await self._handle_new_deal(deal_b24, deal_update)
                    or needs_update
                )
            else:
                needs_update = (
                    await self._handle_exist_deal(
                        deal_b24, deal_db, deal_update
                    )
                    or needs_update
                )
            if needs_update:
                await self._synchronize_deal_data(
                    deal_b24, deal_db, deal_update
                )
        except Exception as e:
            logger.error(f"Error processing deal {external_id}: {str(e)}")
            raise

    async def _synchronize_deal_data(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        deal_update: DealUpdate,
    ) -> None:
        """Синхронизирует данные сделки между Bitrix24 и базой данных"""
        try:
            # Обновляем данные в Bitrix24
            await self.bitrix_client.update(deal_update)

            # Обновляем или создаем запись в базе данных
            if deal_db:
                await self.repo.update(deal_update)
            else:
                await self.repo.create(deal_b24)

            logger.info(
                f"Successfully synchronized deal {deal_b24.external_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to synchronize deal {deal_b24.external_id}: {str(e)}"
            )
            raise

    async def _handle_new_deal(
        self,
        deal_b24: DealCreate,
        deal_update: DealUpdate,
    ) -> bool:
        """Обработка новой сделки"""
        # TODO: Реализовать логику обработки новой сделки
        logger.info(f"Processing new deal: {deal_b24.external_id}")
        return True

    async def _handle_exist_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate,
        deal_update: DealUpdate,
    ) -> bool:
        """Обработка существующей сделки"""
        # TODO: Реализовать логику обработки существующей сделки
        logger.info(f"Processing existing deal: {deal_b24.external_id}")
        return True

    async def _check_source(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        deal_update: DealUpdate,
    ) -> bool:
        """Проверка и определение источника сделки"""
        try:
            needs_update = False
            creation_source_id = deal_b24.creation_source_id
            source_id = deal_b24.source_id
            type_id = deal_b24.type_id

            result = await identify_source(
                deal_b24, self._get_lead, self._get_company, self._get_comments
            )
            creation_source_corr, type_correct, source_correct = result
            logger.info(
                f"{CreationSourceEnum.get_display_name(creation_source_corr)}"
                f":{creation_source_id}, "
                f"{DealTypeEnum.get_display_name(type_correct)}:{type_id}, "
                f"{DealSourceEnum.get_display_name(source_correct)}:"
                f"{source_id}"
            )

            if deal_db is None:  # new deal
                needs_update |= await self._update_field_if_needed(
                    deal_b24,
                    deal_update,
                    "creation_source_id",
                    creation_source_id,
                    creation_source_corr.value,
                )

                needs_update |= await self._update_field_if_needed(
                    deal_b24,
                    deal_update,
                    "source_id",
                    source_id,
                    source_correct.value,
                )

                needs_update |= await self._update_field_if_needed(
                    deal_b24,
                    deal_update,
                    "type_id",
                    type_id,
                    type_correct.value,
                )
                needs_update |= await self._handle_assignment(
                    deal_b24, deal_update, creation_source_corr
                )
                return needs_update
            # TODO: Реализовать логику обработки источников существующей сделки
            return needs_update
        except Exception as e:
            logger.error(
                f"Error identifying source for deal {deal_b24.external_id}: "
                f"{str(e)}"
            )
            raise

    async def _update_field_if_needed(
        self,
        deal_b24: DealCreate,
        deal_update: DealUpdate,
        field_name: str,
        current_value: Any,
        correct_value: Any,
    ) -> bool:
        """
        Обновляет поле сделки, если текущее значение отличается от корректного
        """
        if current_value != correct_value:
            setattr(deal_b24, field_name, correct_value)
            setattr(deal_update, field_name, correct_value)
            logger.info(
                f"Updated {field_name} from {current_value} to {correct_value}"
            )
            return True
        return False

    async def _handle_assignment(
        self,
        deal_b24: DealCreate,
        deal_update: DealUpdate,
        creation_source: CreationSourceEnum,
    ) -> bool:
        """
        Обрабатывает назначение ответственного в зависимости от источника
        сделки
        """
        needs_update = False

        if creation_source == CreationSourceEnum.AUTO:
            if deal_b24.assigned_by_id != WEBSITE_CREATOR:
                deal_b24.assigned_by_id = WEBSITE_CREATOR
                deal_update.assigned_by_id = WEBSITE_CREATOR
                needs_update = True
                logger.info(
                    "Assigned to website creator for auto-created deal"
                )
        else:
            if not await self._check_active_manager(deal_b24.assigned_by_id):
                deal_b24.assigned_by_id = WEBSITE_CREATOR
                deal_update.assigned_by_id = WEBSITE_CREATOR
                needs_update = True
                logger.info(
                    "Reassigned to website creator due to inactive manager"
                )

        return needs_update

    async def _get_lead(self, lead_id: int) -> LeadCreate | None:
        """Получение лида по ID"""
        try:
            lead_service = await self.repo.get_lead_client()
            return await lead_service.bitrix_client.get(lead_id)
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {str(e)}")
            return None

    async def _get_company(
        self,
        company_id: int,
    ) -> CompanyCreate | None:
        """Получение компании по ID"""
        try:
            company_service = await self.repo.get_company_client()
            return await company_service.bitrix_client.get(company_id)
        except Exception as e:
            logger.error(f"Failed to get company {company_id}: {str(e)}")
            return None

    async def _get_comments(
        self,
        deal_id: int,
    ) -> str:
        try:
            timeline_client = self.timeline_comments_bitrix_client
            comments_result = await timeline_client.get_comments_by_entity(
                "deal", deal_id
            )
            comments: list[str] = [
                comm.comment_entity
                for comm in comments_result.result
                if comm.comment_entity
            ]
            return "; ".join(comments)
        except Exception as e:
            logger.error(f"Failed to get comments deal {deal_id}: {str(e)}")
            return ""

    async def _check_active_manager(self, manager_id: int) -> bool:
        """Проверка активных менеджеров"""
        # TODO: Реализовать логику проверки активных менеджеров
        return True
