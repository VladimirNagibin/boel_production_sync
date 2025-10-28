from typing import Any, Generic, Type, TypeVar

from fastapi import status

from core.logger import logger
from core.settings import settings
from schemas.base_schemas import (  # CoreCreateSchema,; CoreUpdateSchema,
    CommonFieldMixin,
    ListResponseSchema,
)

from ..decorators import handle_bitrix_errors
from ..exceptions import BitrixApiError
from .bitrix_api_client import BitrixAPIClient

# Дженерик для схем
# SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=CoreCreateSchema)
# SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=CoreUpdateSchema)
SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=CommonFieldMixin)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=CommonFieldMixin)


class BaseBitrixEntityClient(Generic[SchemaTypeCreate, SchemaTypeUpdate]):
    """Базовый клиент для работы с сущностями Bitrix"""

    entity_name: str
    create_schema: Type[SchemaTypeCreate]
    update_schema: Type[SchemaTypeUpdate]

    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    def _get_method(
        self,
        action: str,
        entity_type_id: int | None,
        crm: bool = True,
    ) -> str:
        """Возвращает имя метода API в зависимости от типа сущности"""
        beginning_request = ""
        if crm:
            beginning_request = "crm."
        return (
            f"{beginning_request}item.{action}"
            if entity_type_id
            else f"{beginning_request}{self.entity_name}.{action}"
        )

    def _prepare_params(
        self,
        entity_id: int | str | None = None,
        data: Any = None,
        entity_type_id: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Подготавливает параметры для API-запроса"""
        # params = kwargs.copy()
        params = {k: v for k, v in kwargs.items() if v is not None}
        if entity_id is not None:
            params["id"] = entity_id

        if data is not None:
            params["fields"] = data.to_bitrix_dict()

        if entity_type_id:
            params["entityTypeId"] = entity_type_id

        return params

    def _handle_response(
        self,
        response: dict[str, Any],
        action: str,
        entity_id: int | str | None = None,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> Any:
        """Обрабатывает ответ API и извлекает данные"""
        result = response.get("result")

        # Для универсальных методов (crm.item.*) данные находятся внутри 'item'
        if entity_type_id and action in {"add", "get"}:
            result = result.get("item") if result else None

        if not crm and action in {"add", "get"}:
            result = result.get("product") if result else None

        if not result:
            error = response.get("error", "Unknown error")
            error_description = response.get(
                "error_description", "Unknown error"
            )
            entity_ref = f"ID={entity_id}" if entity_id else ""
            logger.error(
                f"Failed to {action} {self.entity_name} {entity_ref}: {error}"
            )

            if action == "get":
                raise BitrixApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error=(
                        f"Failed to {action} {self.entity_name} {entity_ref}: "
                        f"{error}"
                    ),
                    error_description=error_description,
                )

            raise BitrixApiError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_description=f"Failed to {action} {self.entity_name}",
            )

        return result

    @handle_bitrix_errors()
    async def create(
        self,
        data: SchemaTypeUpdate,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> int | None:
        """Создание новой сущности"""
        entity_title = getattr(data, "title", "")
        logger.info(f"Creating new {self.entity_name}: {entity_title}")
        method = self._get_method("add", entity_type_id, crm)
        params = self._prepare_params(data=data, entity_type_id=entity_type_id)

        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        result = self._handle_response(response, "add")
        created_id = result["id"] if entity_type_id else result
        logger.info(
            f"{self.entity_name.capitalize()} created successfully: "
            f"ID={created_id}"
        )
        return created_id  # type: ignore[no-any-return]

    @handle_bitrix_errors()
    async def get(
        self,
        entity_id: int | str,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> SchemaTypeCreate:
        """Получение сущности по ID"""
        logger.debug(f"Fetching {self.entity_name} ID={entity_id}")

        method = self._get_method("get", entity_type_id, crm)
        params = self._prepare_params(
            entity_id=entity_id,
            entity_type_id=entity_type_id,
        )
        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        result = self._handle_response(
            response,
            "get",
            entity_id,
            entity_type_id,
            crm,
        )
        return self.create_schema(**result)

    @handle_bitrix_errors()
    async def update(
        self,
        data: SchemaTypeUpdate,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> bool:
        """Обновление сущности"""
        if not data.external_id:
            logger.error("Update failed: Missing entity ID")
            raise ValueError(
                f"{self.entity_name.capitalize()} ID is required for update"
            )

        entity_id = data.external_id
        logger.info(f"Updating {self.entity_name} ID={entity_id}")

        method = self._get_method("update", entity_type_id, crm)
        params = self._prepare_params(
            entity_id=entity_id, data=data, entity_type_id=entity_type_id
        )
        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        # Для универсальных методов возвращается объект, для обычных - булево
        success = bool(
            response.get("result", {}).get("item")
            if entity_type_id
            else response.get("result")
        )

        if success:
            logger.info(
                f"{self.entity_name.capitalize()} updated successfully: "
                f"ID={entity_id}"
            )
        else:
            error = response.get("error", "Unknown error")
            logger.error(
                f"Failed to update {self.entity_name} ID={entity_id}: {error}"
            )

        return success

    @handle_bitrix_errors()
    async def delete(
        self,
        entity_id: int | str,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> bool:
        """Удаление сущности по ID"""
        logger.info(f"Deleting {self.entity_name} ID={entity_id}")

        method = self._get_method("delete", entity_type_id, crm)
        params = self._prepare_params(
            entity_id=entity_id, entity_type_id=entity_type_id
        )

        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        if entity_type_id:
            # Для универсальных методов (crm.item.delete)
            # Успешный ответ может содержать пустой массив в result
            success = "result" in response and response["result"] is not False
        else:
            # Для стандартных методов
            success = response.get("result") is True

        if success:
            logger.info(
                f"{self.entity_name.capitalize()} deleted successfully: "
                f"ID={entity_id}"
            )
        else:
            error = response.get("error", "Unknown error")
            logger.error(
                f"Failed to delete {self.entity_name} ID={entity_id}: {error}"
            )

        return success

    @handle_bitrix_errors()
    async def list(
        self,
        select: list[str] | None = None,
        filter_entity: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        start: int = 0,
        entity_type_id: int | None = None,
        crm: bool = True,
    ) -> ListResponseSchema[SchemaTypeUpdate]:
        """Список сущностей с фильтрацией

        Получает список сущностей из Bitrix24 с возможностью фильтрации,
        сортировки и постраничной выборки.

        Args:
            select: Список полей для выборки.
                - Может содержать маски:
                    '*' - все основные поля (без пользовательских и
                          множественных)
                    'UF_*' - все пользовательские поля (без множественных)
                - По умолчанию выбираются все поля ('*' + 'UF_*')
                - Доступные поля: `crm.{entity_name}.fields`
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
            ListResponseSchema: Объект с результатами выборки:
                - result: список сущностей
                - total: общее количество сущностей
                - next: смещение для следующей страницы (если есть)

        Example:
            Получить сделки с фильтрацией и сортировкой:
            ```python
            deals = await client.list(
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
            f"Fetching {self.entity_name} list: "
            f"select={select}, filter={filter_entity}, "
            f"order={order}, start={start}"
        )

        method = self._get_method("list", entity_type_id, crm)
        params = self._prepare_params(
            entity_type_id=entity_type_id,
            select=select,
            filter=filter_entity,
            order=order,
            start=start,
        )
        response = await self.bitrix_client.call_api(
            method=method, params=params
        )
        result = response.get("result", {})
        # Обработка разных форматов ответа
        if entity_type_id:
            entities = result.get("items", [])
        elif not crm:
            entities = result.get("products", [])
        else:
            entities = result
        total = response.get("total", 0)
        next_page = response.get("next")
        parsed_entities = [self.update_schema(**entity) for entity in entities]
        logger.info(
            f"Fetched {len(parsed_entities)} of {total} {self.entity_name}s"
        )
        return ListResponseSchema[SchemaTypeUpdate](
            result=parsed_entities,
            total=total,
            next=next_page,
        )

    def get_default_create_schema(self, external_id: int | str) -> Any:
        return self.create_schema.get_default_entity(external_id)

    @handle_bitrix_errors()
    async def send_message_b24(
        self, user_id: int, message: str, chat: bool = False
    ) -> bool:
        """Отправка сообщения пользователю в Битрикс24"""
        logger.debug(f"Sending message to {user_id}. Message: {message}")
        params: dict[str, Any] = {}
        if chat:
            params = {
                "CHAT_ID": user_id,
                "message": message,
            }
        else:
            params = {
                "user_id": user_id,
                "message": message,
            }
        try:
            response = await self.bitrix_client.call_api(
                "im.message.add",
                params=params,
            )
            return bool(response.get("result", False))
        except Exception:
            return False

    def get_link(self, external_id: int | str | None) -> str:
        return (
            f"{settings.BITRIX_PORTAL}/crm/{self.entity_name}/details/"
            f"{external_id if external_id else ''}/"
        )

    def get_formatted_link(
        self, external_id: int | str | None, titlt: str
    ) -> str:
        return f"[url={self.get_link(external_id)}]{titlt}[/url]"
