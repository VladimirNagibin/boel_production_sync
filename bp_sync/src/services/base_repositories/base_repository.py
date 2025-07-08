from collections.abc import Awaitable
from typing import Any, Callable, Generic, Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base
from models.bases import IntIdEntity
from schemas.base_schemas import (
    BaseCreateSchema,
    BaseUpdateSchema,
)

# Дженерик для схем
SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=BaseCreateSchema)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=BaseUpdateSchema)
ModelType = TypeVar("ModelType", bound=IntIdEntity)


class BaseRepository(Generic[ModelType, SchemaTypeCreate, SchemaTypeUpdate]):
    """Базовый репозиторий для CRUD операций"""

    model: Type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _exists(self, external_id: int) -> bool:
        """Проверяет существование сущности по external_id"""
        try:
            stmt = select(
                exists().where(self.model.external_id == external_id)
            )
            result = await self.session.execute(stmt)
            return bool(result.scalar())
        except SQLAlchemyError as e:
            logger.exception(
                "Database error checking entity existence "
                f"ID={external_id}: {str(e)}"
            )
            return False

    def _not_found_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для отсутствующей сущности"""
        entity_name = self.model.__name__
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with ID: {external_id} not found",
        )

    def _conflict_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для конфликта дубликатов"""
        entity_name = self.model.__name__
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{entity_name} with ID: {external_id} already exists",
        )

    async def create(
        self,
        data: SchemaTypeCreate,
        pre_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
        post_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> ModelType:
        """Создает новую сделку с проверкой на дубликаты"""
        external_id = data.external_id
        if await self._exists(external_id):
            logger.warning(
                f"Creation {self.model.__name__} conflict: "
                f"ID={external_id} already exists"
            )
            raise self._conflict_exception(external_id)

        try:
            obj = self.model(**data.model_dump())
            self.session.add(obj)

            if pre_commit_hook:
                await pre_commit_hook(obj, data)

            await self.session.flush()

            if post_commit_hook:
                await post_commit_hook(obj, data)

            await self.session.commit()
            await self.session.refresh(obj)
            logger.info(f"{self.model.__name__} created: ID={external_id}")
            return obj
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error creating {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise self._conflict_exception(external_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error creating {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Database operation failed creating {self.model.__name__}"
                ),
            ) from e

    async def get(self, external_id: int) -> Optional[ModelType]:
        try:
            stmt = select(self.model).where(
                self.model.external_id == external_id
            )
            result = await self.session.execute(stmt)
            entity = result.scalar_one_or_none()
            if not entity:
                logger.debug(
                    f"{self.model.__name__} not found: ID={external_id}"
                )
            return entity  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def update(
        self,
        data: SchemaTypeUpdate,
        pre_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
        post_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> ModelType:
        """Обновляет существующую сущность"""
        if not data.external_id:
            logger.error("Update failed: Missing ID")
            raise ValueError("ID is required for update")

        external_id = data.external_id
        if not await self._exists(external_id):
            logger.warning(
                f"Update failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)

        try:
            stmt = (
                update(self.model)
                .where(self.model.external_id == external_id)
                .values(data.model_dump(exclude_unset=True))
                .returning(self.model)
            )

            result = await self.session.execute(stmt)
            obj = result.scalar_one()

            if pre_commit_hook:
                await pre_commit_hook(obj, data)

            if post_commit_hook:
                await post_commit_hook(obj, data)

            await self.session.commit()
            logger.info(f"{self.model.__name__} updated: ID={external_id}")
            return obj  # type: ignore[no-any-return]
        except NoResultFound:
            await self.session.rollback()
            logger.warning(
                f"Update failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error updating {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def delete(
        self,
        external_id: int,
        pre_delete_hook: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> bool:
        """Удаляет сущность по external_id, возвращает статус операции"""
        if not await self._exists(external_id):
            logger.warning(
                f"Delete failed: {self.model.__name__} "
                f"ID={external_id} not found"
            )
            raise self._not_found_exception(external_id)

        try:
            if pre_delete_hook:
                await pre_delete_hook(external_id)

            stmt = delete(self.model).where(
                self.model.external_id == external_id
            )
            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                raise self._not_found_exception(external_id)

            await self.session.commit()
            logger.info(f"{self.model.__name__} deleted: ID={external_id}")
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error deleting {self.model.__name__} "
                f"ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed",
            ) from e

    async def _check_object_exists(
        self, model: Type[Base], **filters: Any
    ) -> bool:
        """Проверяет существование объекта в БД по заданным фильтрам"""
        stmt = select(model).filter_by(**filters).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
