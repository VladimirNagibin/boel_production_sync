from typing import Any

from fastapi import Depends, HTTPException, status

from core.logger import logger
from schemas.deal_schemas import DealCreate, DealListResponse, DealUpdate

from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..decorators import handle_bitrix_errors
from ..dependencies import get_bitrix_client
from ..exceptions import BitrixApiError


class DealBitrixClient:
    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    @handle_bitrix_errors()
    async def create_deal(self, deal_data: DealUpdate) -> int | None:
        """Создание новой сделки"""
        logger.info(f"Creating new deal: {deal_data.title}")
        result = await self.bitrix_client.call_api(
            "crm.deal.add", {"fields": deal_data.to_bitrix_dict()}
        )
        if deal_id := result.get("result"):
            logger.info(f"Deal created successfully: ID={deal_id}")
            return deal_id  # type: ignore[no-any-return]
        logger.error(
            f"Failed to create deal: {deal_data.model_dump()}"
            f"{result.get('error', 'Unknown error')}"
        )
        raise BitrixApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_description="Failed to create deal.",
        )

    @handle_bitrix_errors()
    async def get_deal(self, deal_id: int) -> DealCreate:
        """Получение сделки по ID"""
        logger.debug(f"Fetching deal ID={deal_id}")
        response = await self.bitrix_client.call_api(
            "crm.deal.get", {"id": deal_id}
        )
        if not (deal_data := response.get("result")):
            logger.warning(f"Deal not found: ID={deal_id}")
            raise HTTPException(status_code=404, detail="Deal not found")
        return DealCreate(**deal_data)

    @handle_bitrix_errors()
    async def update_deal(self, deal_data: DealUpdate) -> bool:
        """Обновление сделки"""
        if not deal_data.external_id:
            logger.error("Update failed: Missing deal ID")
            raise ValueError("Deal ID is required for update")

        deal_id = deal_data.external_id
        logger.info(f"Updating deal ID={deal_id}")
        result = await self.bitrix_client.call_api(
            "crm.deal.update",
            {"id": deal_id, "fields": deal_data.to_bitrix_dict()},
        )

        if success := result.get("result", False):
            logger.info(f"Deal updated successfully: ID={deal_id}")
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to update deal ID={deal_id}: {error}")
        return success  # type: ignore[no-any-return]

    @handle_bitrix_errors()
    async def delete_deal(self, deal_id: int) -> bool:
        """Удаление сделки по ID"""
        logger.info(f"Deleting deal ID={deal_id}")
        result = await self.bitrix_client.call_api(
            "crm.deal.delete", {"id": deal_id}
        )

        if success := result.get("result", False):
            logger.info(f"Deal deleted successfully: ID={deal_id}")
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to delete deal ID={deal_id}: {error}")

        return success  # type: ignore[no-any-return]

    @handle_bitrix_errors()
    async def list_deals(
        self,
        select: list[str] | None = None,
        filter_deals: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        start: int = 0,
    ) -> DealListResponse:
        """Список сделок с фильтрацией

        Получает список сделок из Bitrix24 с возможностью фильтрации,
        сортировки и постраничной выборки.

        Args:
            select: Список полей для выборки.
                - Может содержать маски:
                    '*' - все основные поля (без пользовательских и
                          множественных)
                    'UF_*' - все пользовательские поля (без множественных)
                - По умолчанию выбираются все поля ('*' + 'UF_*')
                - Доступные поля: `crm.deal.fields`
                - Пример: ["ID", "TITLE", "OPPORTUNITY"]

            filter: Фильтр для выборки сделок.
                - Формат: {поле: значение}
                - Поддерживаемые префиксы для операторов:
                    '>=' - больше или равно
                    '>'  - больше
                    '<=' - меньше или равно
                    '<'  - меньше
                    '@'  - IN (значение должно быть массивом)
                    '!@' - NOT IN (значение должно быть массивом)
                    '%'  - LIKE (поиск подстроки, % не нужен)
                    '=%' - LIKE с указанием позиции (% в начале)
                    '=%%' - LIKE с указанием позиции (% в конце)
                    '=%%%' - LIKE с подстрокой в любой позиции
                    '='  - равно (по умолчанию)
                    '!=' - не равно
                    '!'  - не равно
                - Не работает с полями типа crm_status, crm_contact ...
                - Пример: {">OPPORTUNITY": 1000, "CATEGORY_ID": 1}

            order: Сортировка результатов.
                - Формат: {поле: направление}
                - Направление: "ASC" (по возрастанию) или "DESC" (по убыванию)
                - Пример: {"TITLE": "ASC", "DATE_CREATE": "DESC"}

            start: Смещение для постраничной выборки.
                - Размер страницы фиксирован: 50 записей
                - Формула: start = (N-1) * 50, где N - номер страницы
                - Пример: для 2-й страницы передать 50

        Returns:
            DealListResponse: Объект с результатами выборки:
                - result: список сделок
                - total: общее количество сделок
                - next: смещение для следующей страницы (если есть)

        Example:
            Получить сделки с фильтрацией и сортировкой:
            ```python
            deals = await client.list_deals(
                select=["ID", "TITLE", "OPPORTUNITY"],
                filter={
                    "CATEGORY_ID": 1,
                    ">OPPORTUNITY": 10000,
                    "<=OPPORTUNITY": 20000,
                    "@ASSIGNED_BY_ID": [1, 6]
                },
                order={"OPPORTUNITY": "ASC"},
                start=0
            )
            ```

        Bitrix API Example:
            ```bash
            curl -X POST \\
            -H "Content-Type: application/json" \\
            -H "Accept: application/json" \\
            -d '{
                "SELECT": ["ID", "TITLE", "OPPORTUNITY"],
                "FILTER": {
                    "CATEGORY_ID": 1,
                    ">OPPORTUNITY": 10000,
                    "<=OPPORTUNITY": 20000,
                    "@ASSIGNED_BY_ID": [1, 6]
                },
                "ORDER": {"OPPORTUNITY": "ASC"},
                "start": 0
            }' \\
            https://example.bitrix24.ru/rest/user_id/webhook/crm.deal.list
            ```
        """
        logger.debug(
            f"Fetching deals list: "
            f"select={select}, filter={filter_deals}, "
            f"order={order}, start={start}"
        )

        params: dict[str, Any] = {}
        if select:
            params["select"] = select
        if filter_deals:
            params["filter"] = filter_deals
        if order:
            params["order"] = order
        if start:
            params["start"] = start

        response = await self.bitrix_client.call_api("crm.deal.list", params)

        deals = [DealUpdate(**deal) for deal in response.get("result", [])]
        total = response.get("total", 0)
        next_page = response.get("next")

        logger.info(f"Fetched {len(deals)} of {total} deals")
        return DealListResponse(
            result=deals,
            total=total,
            next=next_page,
        )


def get_deal_bitrix_client(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
) -> DealBitrixClient:
    return DealBitrixClient(bitrix_client)
