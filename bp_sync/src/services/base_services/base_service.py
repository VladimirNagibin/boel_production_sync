from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar

from core.logger import logger
from models.bases import IntIdEntity

from ..exceptions import BitrixApiError, ConflictException, CyclicCallException

ExternalIdType = TypeVar("ExternalIdType", int, str)


class BitrixClientProtocol(Protocol):
    """Протокол для клиента Bitrix API"""

    @abstractmethod
    async def get(
        self, entity_id: str | int, entity_type_id: int | None = None
    ) -> Any:
        """Получает сущность по ID из Bitrix"""
        ...

    @abstractmethod
    def get_default_create_schema(self, external_id: int | str) -> Any:
        """Получает дефолтную схему для создания сущности"""
        ...


class RepositoryProtocol(Protocol):
    """Протокол для репозитория"""

    @abstractmethod
    async def create_entity(self, data: Any) -> Any:
        """Создает сущность в БД"""
        ...

    @abstractmethod
    async def update_entity(self, data: Any) -> Any:
        """Обновляет сущность в БД"""
        ...

    @abstractmethod
    async def delete(self, external_id: Any) -> bool:
        """Удаляет сущность по ID"""
        ...

    @abstractmethod
    async def set_deleted_in_bitrix(
        self, external_id: Any, is_deleted: bool = True
    ) -> bool:
        """Помечает сущность как удаленную в Bitrix"""
        ...

    @abstractmethod
    async def get(self, external_id: Any) -> Any | None:
        """Получает сущность по ID"""
        ...


T = TypeVar("T", bound=IntIdEntity)  # Тип для сущности базы данных
R = TypeVar("R", bound=RepositoryProtocol)  # Тип для репозитория
C = TypeVar("C", bound=BitrixClientProtocol)  # Тип для Bitrix клиента


class BaseEntityClient(ABC, Generic[T, R, C]):
    """Базовый сервис для работы с сущностями"""

    @property
    @abstractmethod
    def entity_name(self) -> str:
        """Имя сущности для логирования"""
        pass

    @property
    @abstractmethod
    def bitrix_client(self) -> C:
        """Клиент для работы с Bitrix API"""
        pass

    @property
    @abstractmethod
    def repo(self) -> R:
        """Репозиторий для работы с базой данных"""
        pass

    async def import_from_bitrix(
        self, entity_id: ExternalIdType, entity_type_id: int | None = None
    ) -> tuple[T, bool]:
        """Импортирует сущность из Bitrix в базу данных"""

        from ..dependencies import get_creation_cache, get_update_needed_cache

        creation_cache = get_creation_cache()
        update_needed_cache = get_update_needed_cache()
        entity_key = (self.repo.model, entity_id)  # type: ignore[attr-defined]
        if entity_key in creation_cache.keys():
            raise CyclicCallException
        creation_cache[entity_key] = True
        logger.info(
            f"Starting {self.entity_name} import from Bitrix",
            extra={f"{self.entity_name}_id": entity_id},
        )
        try:
            entity_data = await self.bitrix_client.get(
                entity_id, entity_type_id=entity_type_id
            )
        except BitrixApiError as e:
            if e.is_not_found_error():
                entity_data = self.bitrix_client.get_default_create_schema(
                    entity_id
                )
                logger.warning(
                    f"Can't retrieved {self.entity_name} data from Bitrix",
                    extra={
                        f"{self.entity_name}_id": entity_id,
                        "data": entity_data.model_dump(),
                    },
                )
            else:
                raise

        logger.debug(
            f"Retrieved {self.entity_name} data from Bitrix",
            extra={
                f"{self.entity_name}_id": entity_id,
                "data": entity_data.model_dump(),
            },
        )
        try:
            entity_db = await self.repo.create_entity(entity_data)
        except ConflictException:
            entity_db = await self.repo.update_entity(entity_data)
        logger.info(
            f"Successfully imported {self.entity_name} from Bitrix",
            extra={f"{self.entity_name}_id": entity_id, "db_id": entity_db.id},
        )
        update_needed = bool(update_needed_cache)
        return entity_db, update_needed

    async def refresh_from_bitrix(
        self, entity_id: int | str, entity_type_id: int | None = None
    ) -> T:
        """Обновляет данные сущности из Bitrix в базе данных"""

        from ..dependencies import get_creation_cache

        creation_cache = get_creation_cache()
        entity_key = (self.repo.model, entity_id)  # type: ignore[attr-defined]
        if entity_key in creation_cache.keys():
            raise CyclicCallException
        creation_cache[entity_key] = True

        logger.info(
            f"Refreshing {self.entity_name} data from Bitrix",
            extra={f"{self.entity_name}_id": entity_id},
        )
        try:
            entity_data = await self.bitrix_client.get(
                entity_id, entity_type_id=entity_type_id
            )
        except BitrixApiError as e:
            if e.is_not_found_error():
                # await self.set_deleted_in_bitrix(entity_id)
                entity_data = self.bitrix_client.get_default_create_schema(
                    entity_id
                )
                logger.warning(
                    f"Can't retrieved {self.entity_name} data from Bitrix",
                    extra={
                        f"{self.entity_name}_id": entity_id,
                        "data": entity_data.model_dump(),
                    },
                )
            else:
                raise

        logger.debug(
            f"Retrieved updated {self.entity_name} data from Bitrix",
            extra={
                f"{self.entity_name}_id": entity_id,
                "data": entity_data.model_dump(),
            },
        )

        entity_db = await self.repo.update_entity(entity_data)
        logger.info(
            f"Successfully refreshed {self.entity_name} data from Bitrix",
            extra={f"{self.entity_name}_id": entity_id, "db_id": entity_db.id},
        )
        return entity_db  # type: ignore[no-any-return]

    async def delete_entity(self, entity_id: int) -> bool:
        """Удаляет сущность по ID"""
        try:
            return await self.repo.delete(entity_id)
        except Exception:
            return False

    async def set_deleted_in_bitrix(
        self, external_id: int | str, is_deleted: bool = True
    ) -> bool:
        """Помечает сущность как удаленную в Bitrix"""
        try:
            return await self.repo.set_deleted_in_bitrix(
                external_id, is_deleted
            )
        except Exception:
            return False

    async def get_changes_b24_db(
        self,
        entity_id: ExternalIdType,
        entity_type_id: int | None = None,
        exclude_fields: set[str] | None = None,
    ) -> tuple[Any, Any, dict[str, dict[str, Any]] | None]:
        schema_b24 = await self.bitrix_client.get(entity_id, entity_type_id)
        schema_db = await self.repo.get(entity_id)

        if schema_db is None:
            return schema_b24, schema_db, None

        if not hasattr(schema_db, "to_pydantic"):
            logger.warning(
                f"Entity {schema_db} does not have to_pydantic method"
            )
            raise AttributeError(
                f"Missing 'to_pydantic' method on {type(schema_db).__name__}"
            )

        # Проверяем, что schema_b24 имеет метод get_changes
        if not hasattr(schema_b24, "get_changes"):
            logger.warning(
                f"Schema {schema_b24} does not have get_changes method"
            )
            raise AttributeError(
                f"Missing 'get_changes' method on {type(schema_b24).__name__}"
            )

        pydantic_db = schema_db.to_pydantic()

        # Проверяем, что pydantic_db того же типа, что и schema_b24
        if not isinstance(pydantic_db, type(schema_b24)):
            logger.warning("Type mismatch between Bitrix schema and DB entity")
            raise TypeError(
                f"Type mismatch: expected {type(schema_b24).__name__}, "
                f"got {type(pydantic_db).__name__}"
            )

        return (
            schema_b24,
            schema_db,
            schema_b24.get_changes(pydantic_db, exclude_fields=exclude_fields),
        )
