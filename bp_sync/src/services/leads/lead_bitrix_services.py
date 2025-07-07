from fastapi import Depends

from schemas.lead_schemas import LeadCreate, LeadUpdate  # , LeadListResponse

from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..bitrix_services.entity_bitrix_services import BaseBitrixEntityClient
from ..dependencies import get_bitrix_client


class LeadBitrixClient(BaseBitrixEntityClient[LeadCreate, LeadUpdate]):
    entity_name = "lead"
    create_schema = LeadCreate
    update_schema = LeadUpdate

    """
    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    @handle_bitrix_errors()
    async def create_lead(self, lead_data: LeadUpdate) -> int | None:
        "Создание нового лида"
        logger.info(f"Creating new lead: {lead_data.title}")
        result = await self.bitrix_client.call_api(
            "crm.lead.add", {"fields": lead_data.to_bitrix_dict()}
        )
        if lead_id := result.get("result"):
            logger.info(f"Lead created successfully: ID={lead_id}")
            return lead_id  # type: ignore[no-any-return]
        logger.error(
            f"Failed to create deal: {lead_data.model_dump()}"
            f"{result.get('error', 'Unknown error')}"
        )
        raise BitrixApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_description="Failed to create deal.",
        )

    @handle_bitrix_errors()
    async def get_lead(self, lead_id: int) -> LeadCreate:
        "Получение лида по ID"
        logger.debug(f"Fetching lead ID={lead_id}")
        response = await self.bitrix_client.call_api(
            "crm.lead.get", {"id": lead_id}
        )
        if not (lead_data := response.get("result")):
            logger.warning(f"Lead not found: ID={lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")
        return LeadCreate(**lead_data)

    @handle_bitrix_errors()
    async def update_lead(self, lead_data: LeadUpdate) -> bool:
        "Обновление лида"
        if not lead_data.external_id:
            logger.error("Update failed: Missing lead ID")
            raise ValueError("Lead ID is required for update")

        lead_id = lead_data.external_id
        logger.info(f"Updating lead ID={lead_id}")
        result = await self.bitrix_client.call_api(
            "crm.lead.update",
            {"id": lead_id, "fields": lead_data.to_bitrix_dict()},
        )

        if success := result.get("result", False):
            logger.info(f"Lead updated successfully: ID={lead_id}")
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to update lead ID={lead_id}: {error}")
        return success  # type: ignore[no-any-return]

    @handle_bitrix_errors()
    async def delete_lead(self, lead_id: int) -> bool:
        "Удаление лида по ID"
        logger.info(f"Deleting lead ID={lead_id}")
        result = await self.bitrix_client.call_api(
            "crm.lead.delete", {"id": lead_id}
        )

        if success := result.get("result", False):
            logger.info(f"Lead deleted successfully: ID={lead_id}")
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to delete lead ID={lead_id}: {error}")

        return success  # type: ignore[no-any-return]
    """
    """
    @handle_bitrix_errors()
    async def list_leads(
        self,
        select: list[str] | None = None,
        filter_leads: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        start: int = 0,
    ) -> LeadListResponse:
    """
    """Список лидов с фильтрацией

        Получает список лидов из Bitrix24 с возможностью фильтрации,
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
            LeadListResponse: Объект с результатами выборки:
                - result: список сделок
                - total: общее количество сделок
                - next: смещение для следующей страницы (если есть)

        Example:
            Получить лиды с фильтрацией и сортировкой:
            ```python
            leads = await client.list_leads(
                select=["ID", "TITLE", "OPPORTUNITY"],
                filter={
                    "SOURCE_ID": 1,
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
                    "SOURCE_ID": 1,
                    ">OPPORTUNITY": 10000,
                    "<=OPPORTUNITY": 20000,
                    "@ASSIGNED_BY_ID": [1, 6]
                },
                "ORDER": {"OPPORTUNITY": "ASC"},
                "start": 0
            }' \\
            https://example.bitrix24.ru/rest/user_id/webhook/crm.lead.list
            ```
        """
    """
        logger.debug(
            f"Fetching leads list: "
            f"select={select}, filter={filter_leads}, "
            f"order={order}, start={start}"
        )

        params: dict[str, Any] = {}
        if select:
            params["select"] = select
        if filter_leads:
            params["filter"] = filter_leads
        if order:
            params["order"] = order
        if start:
            params["start"] = start

        response = await self.bitrix_client.call_api("crm.lead.list", params)

        leads = [LeadUpdate(**lead) for lead in response.get("result", [])]
        total = response.get("total", 0)
        next_page = response.get("next")

        logger.info(f"Fetched {len(leads)} of {total} deals")
        return LeadListResponse(
            result=leads,
            total=total,
            next=next_page,
        )
        """


def get_lead_bitrix_client(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
) -> LeadBitrixClient:
    return LeadBitrixClient(bitrix_client)
