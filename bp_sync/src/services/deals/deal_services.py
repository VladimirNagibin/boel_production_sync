from datetime import datetime
from typing import Any

from fastapi import HTTPException

from core.logger import logger
from models.deal_models import Deal as DealDB
from schemas.company_schemas import CompanyCreate
from schemas.deal_schemas import DealCreate
from schemas.lead_schemas import LeadCreate

from ..base_services.base_service import BaseEntityClient
from ..timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from .deal_bitrix_services import DealBitrixClient
from .deal_repository import DealRepository
from .enums import CreationSourceEnum, DealSourceEnum, DealTypeEnum
from .handling_helpers import identify_source
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
            deal_b24, deal_db, changes = await self.get_changes_b24_db(
                external_id
            )
            await self._check_source(deal_b24)
            if deal_db is None:  # not in database
                await self._handle_new_deal(deal_b24)
            else:
                await self._handle_exist_deal(deal_b24, deal_db)
            print(changes)
        except Exception as e:
            logger.error(f"Error processing deal {external_id}: {str(e)}")
            raise

    async def _handle_new_deal(self, deal_b24: DealCreate) -> None:
        """Обработка новой сделки"""
        ...
        logger.info(f"Processing new deal: {deal_b24.external_id}")

    async def _handle_exist_deal(
        self, deal_b24: DealCreate, deal_db: DealCreate
    ) -> None:
        """Обработка существующей сделки"""
        ...
        logger.info(f"Processing existing deal: {deal_b24.external_id}")

    async def _check_source(self, deal_b24: DealCreate) -> None:
        """Проверка и определение источника сделки"""
        try:
            creation_source_id = deal_b24.creation_source_id
            source_id = deal_b24.source_id
            type_id = deal_b24.type_id

            result = await identify_source(
                deal_b24, self._get_lead, self._get_company, self._get_comments
            )
            creation_source_reciv, type_reciv, source_reciv = result
            logger.info(
                f"{CreationSourceEnum.get_display_name(creation_source_reciv)}"
                f":{creation_source_id}, "
                f"{DealTypeEnum.get_display_name(type_reciv)}:{type_id}, "
                f"{DealSourceEnum.get_display_name(source_reciv)}:{source_id}"
            )
        except Exception as e:
            logger.error(
                f"Error identifying source for deal {deal_b24.external_id}: "
                f"{str(e)}"
            )
            raise

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
