from typing import Any, Generic, Type, TypeVar

from fastapi import HTTPException, status

from core.logger import logger
from schemas.base_schemas import (
    BaseCreateSchema,
    BaseUpdateSchema,
    ListResponseSchema,
)

from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..decorators import handle_bitrix_errors
from ..exceptions import BitrixApiError

# Дженерик для схем
SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=BaseCreateSchema)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=BaseUpdateSchema)


class BaseBitrixEntityClient(Generic[SchemaTypeCreate, SchemaTypeUpdate]):
    """Базовый клиент для работы с сущностями Bitrix"""

    entity_name: str
    create_schema: Type[SchemaTypeCreate]
    update_schema: Type[SchemaTypeUpdate]

    def __init__(self, bitrix_client: BitrixAPIClient):
        self.bitrix_client = bitrix_client

    @handle_bitrix_errors()
    async def create(self, data: SchemaTypeUpdate) -> int | None:
        """Создание новой сущности"""
        entity_title = getattr(data, "title", "")
        logger.info(f"Creating new {self.entity_name}: {entity_title}")
        result = await self.bitrix_client.call_api(
            f"crm.{self.entity_name}.add", {"fields": data.to_bitrix_dict()}
        )
        if entity_id := result.get("result"):
            logger.info(
                f"{self.entity_name.capitalize()} created successfully: "
                f"ID={entity_id}"
            )
            return entity_id  # type: ignore[no-any-return]
        logger.error(
            f"Failed to create {self.entity_name}: {data.model_dump()}"
            f"{result.get('error', 'Unknown error')}"
        )
        raise BitrixApiError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_description=f"Failed to create {self.entity_name}.",
        )

    @handle_bitrix_errors()
    async def get(self, entity_id: int) -> SchemaTypeCreate:
        """Получение сущности по ID"""
        logger.debug(f"Fetching {self.entity_name} ID={entity_id}")
        response = await self.bitrix_client.call_api(
            f"crm.{self.entity_name}.get", {"id": entity_id}
        )
        if not (entity_data := response.get("result")):
            logger.warning(
                f"{self.entity_name.capitalize()} not found: ID={entity_id}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"{self.entity_name.capitalize()} not found",
            )
        return self.create_schema(**entity_data)

    @handle_bitrix_errors()
    async def update(self, data: SchemaTypeUpdate) -> bool:
        """Обновление сущности"""
        if not data.external_id:
            logger.error("Update failed: Missing entity ID")
            raise ValueError(
                f"{self.entity_name.capitalize()} ID is required for update"
            )

        entity_id = data.external_id
        logger.info(f"Updating {self.entity_name} ID={entity_id}")
        result = await self.bitrix_client.call_api(
            f"crm.{self.entity_name}.update",
            {"id": entity_id, "fields": data.to_bitrix_dict()},
        )

        if success := result.get("result", False):
            logger.info(
                f"{self.entity_name.capitalize()} updated successfully: "
                f"ID={entity_id}"
            )
        else:
            error = result.get("error", "Unknown error")
            logger.error(
                f"Failed to update {self.entity_name} ID={entity_id}: {error}"
            )
        return bool(success)

    @handle_bitrix_errors()
    async def delete(self, entity_id: int) -> bool:
        """Удаление сущности по ID"""
        logger.info(f"Deleting {self.entity_name} ID={entity_id}")
        result = await self.bitrix_client.call_api(
            f"crm.{self.entity_name}.delete", {"id": entity_id}
        )

        if success := result.get("result", False):
            logger.info(
                f"{self.entity_name.capitalize()} deleted successfully: "
                f"ID={entity_id}"
            )
        else:
            error = result.get("error", "Unknown error")
            logger.error(
                f"Failed to delete {self.entity_name} ID={entity_id}: {error}"
            )

        return bool(success)

    @handle_bitrix_errors()
    async def list(
        self,
        select: list[str] | None = None,
        filter_entity: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        start: int = 0,
    ) -> ListResponseSchema:  # type: ignore[type-arg]
        """Список сущностей с фильтрацией"""
        logger.debug(
            f"Fetching {self.entity_name} list: "
            f"select={select}, filter={filter_entity}, "
            f"order={order}, start={start}"
        )

        params: dict[str, Any] = {}
        if select:
            params["select"] = select
        if filter_entity:
            params["filter"] = filter_entity
        if order:
            params["order"] = order
        if start:
            params["start"] = start

        response = await self.bitrix_client.call_api(
            f"crm.{self.entity_name}.list", params
        )

        entities = [
            self.update_schema(**entity)
            for entity in response.get("result", [])
        ]
        total = response.get("total", 0)
        next_page = response.get("next")

        logger.info(f"Fetched {len(entities)} of {total} {self.entity_name}s")
        return ListResponseSchema(
            result=entities,
            total=total,
            next=next_page,
        )
