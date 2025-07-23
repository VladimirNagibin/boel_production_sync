from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar

from core.logger import logger
from models.bases import IntIdEntity

from ..exceptions import BitrixApiError


class BitrixClientProtocol(Protocol):
    """Протокол для клиента Bitrix API"""

    @abstractmethod
    async def get(
        self, entity_id: int, entity_type_id: int | None = None
    ) -> Any:
        """Получает сущность по ID из Bitrix"""
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
    async def delete(self, external_id: int | str) -> bool:
        """Удаляет сущность по ID"""
        ...

    @abstractmethod
    async def set_deleted_in_bitrix(
        self, external_id: int | str, is_deleted: bool = True
    ) -> bool:
        """Помечает сущность как удаленную в Bitrix"""
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
        self, entity_id: int, entity_type_id: int | None = None
    ) -> T:
        """Импортирует сущность из Bitrix в базу данных"""
        logger.info(
            f"Starting {self.entity_name} import from Bitrix",
            extra={f"{self.entity_name}_id": entity_id},
        )
        entity_data = await self.bitrix_client.get(
            entity_id, entity_type_id=entity_type_id
        )
        logger.debug(
            f"Retrieved {self.entity_name} data from Bitrix",
            extra={
                f"{self.entity_name}_id": entity_id,
                "data": entity_data.model_dump(),
            },
        )
        entity_db = await self.repo.create_entity(entity_data)
        logger.info(
            f"Successfully imported {self.entity_name} from Bitrix",
            extra={f"{self.entity_name}_id": entity_id, "db_id": entity_db.id},
        )
        return entity_db  # type: ignore[no-any-return]

    async def refresh_from_bitrix(
        self, entity_id: int, entity_type_id: int | None = None
    ) -> T:
        """Обновляет данные сущности из Bitrix в базе данных"""
        logger.info(
            f"Refreshing {self.entity_name} data from Bitrix",
            extra={f"{self.entity_name}_id": entity_id},
        )
        try:
            entity_data = await self.bitrix_client.get(
                entity_id, entity_type_id=entity_type_id
            )
            # test
            # from schemas.lead_schemas import LeadUpdate
            # from schemas.deal_schemas import DealUpdate
            # print(entity_data)
            # res2 = LeadUpdate(
            #    **entity_data.model_dump(by_alias=True, exclude_unset=True)
            # )
            # print(res2.to_bitrix_dict())
            # test //
        except BitrixApiError as e:
            if e.is_not_found_error():
                await self.set_deleted_in_bitrix(entity_id)
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
        self, external_id: int, is_deleted: bool = True
    ) -> bool:
        """Помечает сущность как удаленную в Bitrix"""
        try:
            return await self.repo.set_deleted_in_bitrix(
                external_id, is_deleted
            )
        except Exception:
            return False
