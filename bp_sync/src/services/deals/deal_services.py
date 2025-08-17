from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd
from fastapi import HTTPException

from core.logger import logger
from models.deal_models import Deal as DealDB

from ..base_services.base_service import BaseEntityClient
from .deal_bitrix_services import DealBitrixClient
from .deal_repository import DealRepository


class DealClient(BaseEntityClient[DealDB, DealRepository, DealBitrixClient]):
    def __init__(
        self,
        deal_bitrix_client: DealBitrixClient,
        deal_repo: DealRepository,
    ):
        self._bitrix_client = deal_bitrix_client
        self._repo = deal_repo

    @property
    def entity_name(self) -> str:
        return "deal"

    @property
    def bitrix_client(self) -> DealBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> DealRepository:
        return self._repo

    async def _prepare_data(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Подготавливает данные для экспорта"""
        deals = await self.repo.fetch_deals(start_date, end_date)
        if not deals:
            logger.warning(f"No deals found for {start_date}-{end_date}")
            raise HTTPException(
                status_code=404, detail="No deals found in specified period"
            )

        return [await self._process_deal_row(deal) for deal in deals]

    async def _process_deal_row(self, deal: DealDB) -> dict[str, Any]:
        """Обрабатывает одну сделку для экспорта"""
        row = self.repo.build_data_row(deal)
        return {
            key: self._repo.convert_to_naive_datetime(value)
            for key, value in row.items()
        }

    async def _create_dataframe(
        self, data: list[dict[str, Any]]
    ) -> pd.DataFrame:
        df = pd.DataFrame(data)
        logger.info(f"Created DataFrame with {len(df)} rows")

        df = df.sort_values(
            by=["Дата сделки", "Ответственный по сделке", "Сумма сделки"],
            ascending=[
                True,  # deal_date_create: по возрастанию (старые -> новые)
                True,  # deal_assigned_by_id: A->Я
                False,  # deal_opportunity: по убыванию (крупные сначала)
            ],
            na_position="last",  # поместить пустые значения в конец
            # inplace=True,
        )
        return df

    async def _create_excel_file(self, df: pd.DataFrame) -> str:
        """Создает временный Excel-файл"""
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            return tmp.name

    async def export_deals_to_excel(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Основной метод экспорта сделок в Excel"""
        try:
            logger.info(f"Exporting deals from {start_date} to {end_date}")
            data = await self._prepare_data(start_date, end_date)
            df = await self._create_dataframe(data)
            return await self._create_excel_file(df)
        except Exception as e:
            logger.error(f"Export failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Export error: {str(e)}"
            ) from e
