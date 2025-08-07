from collections.abc import Awaitable
from typing import Any, Callable, Generic, Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base
from models.bases import IntIdEntity, NameStrIdEntity
from schemas.base_schemas import (  # BaseCreateSchema,; BaseUpdateSchema,
    CommonFieldMixin,
)

# from ..dependencies import get_exists_cache
from ..exceptions import ConflictException

# Дженерик для схем
SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=CommonFieldMixin)
SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=CommonFieldMixin)
# SchemaTypeCreate = TypeVar("SchemaTypeCreate", bound=BaseCreateSchema)
# SchemaTypeUpdate = TypeVar("SchemaTypeUpdate", bound=BaseUpdateSchema)
ModelType = TypeVar("ModelType", bound=IntIdEntity | NameStrIdEntity)


class BaseRepository(Generic[ModelType, SchemaTypeCreate, SchemaTypeUpdate]):
    """Базовый репозиторий для CRUD операций"""

    model: Type[ModelType]
    _default_related_checks: list[tuple[str, Type[Base], str]] = []
    """
    Список проверок по умолчанию в формате:
    (атрибут_схемы, модель_бд, поле_модели)
    """
    _default_related_create: dict[str, tuple[Any, Any, bool]] = {}
    """
    Словарь проверок с созданием сущности по умолчанию в формате:
    {атрибут_схемы: (клиент, модель_бд, проверка обязательна )}
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _exists(self, external_id: int | str) -> bool:
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

    def _not_found_exception(self, external_id: int | str) -> HTTPException:
        """Генерирует исключение для отсутствующей сущности"""
        entity_name = self.model.__name__
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with ID: {external_id} not found",
        )

    def _conflict_exception(self, external_id: int | str) -> ConflictException:
        """Генерирует исключение для конфликта дубликатов"""
        entity_name = self.model.__name__
        return ConflictException(entity_name, external_id)

    async def create(
        self,
        data: SchemaTypeCreate,
        pre_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
        post_commit_hook: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> ModelType:
        """Создает новую сделку с проверкой на дубликаты"""
        if not data.external_id:
            logger.error("Update failed: Missing ID")
            raise ValueError("ID is required for update")
        external_id = data.external_id
        if await self._exists(external_id):
            logger.warning(
                f"Creation {self.model.__name__} conflict: "
                f"ID={external_id} already exists"
            )
            raise self._conflict_exception(external_id)
        print(f"Creation {self.model.__name__}, ID={external_id}")
        try:
            obj = self.model(**data.model_dump_db())
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

    async def get(self, external_id: int | str) -> Optional[ModelType]:
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
        data: SchemaTypeUpdate | SchemaTypeCreate,
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
                .values(data.model_dump_db(exclude_unset=True))
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
        external_id: int | str,
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
        """Проверяет существование объекта в БД с кэшированием результатов"""
        from ..dependencies import get_exists_cache

        # Создаем уникальный ключ для кэша
        cache_key = (model, tuple(sorted(filters.items())))

        # Получаем кэш из контекста запроса
        cache = get_exists_cache()

        # Если результат уже в кэше - возвращаем его
        if cache_key in cache:
            return cache[cache_key]

        # Выполняем запрос, если нет в кэше
        stmt = select(model).filter_by(**filters).limit(1)
        result = await self.session.execute(stmt)
        exists = result.scalar_one_or_none() is not None

        # Сохраняем результат в кэш
        cache[cache_key] = exists
        return exists

    async def set_deleted_in_bitrix(  # Добавить запись None в ссылках
        self, external_id: int | str, is_deleted: bool = True
    ) -> bool:
        """
        Устанавливает флаг is_deleted_in_bitrix для сущности по external_id
        :param external_id: ID во внешней системе
        :param is_deleted: новое значение флага удаления
        :return: True, если обновление прошло успешно
        """
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
                .values(is_deleted_in_bitrix=is_deleted)
                .execution_options(synchronize_session="fetch")
            )

            result = await self.session.execute(stmt)

            if result.rowcount == 0:
                logger.warning(
                    f"{self.model.__name__} with external_id={external_id} "
                    "not found"
                )
                return False

            await self.session.commit()
            logger.info(
                f"{self.model.__name__} ID={external_id} marked as "
                f"deleted={is_deleted}"
            )
            return True
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

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return self._default_related_checks

    async def _check_related_objects(
        self,
        data: SchemaTypeCreate | SchemaTypeUpdate,
        additional_checks: Optional[list[tuple[str, Type[Base], str]]] = None,
    ) -> None:
        """Проверяет существование связанных объектов"""
        errors: list[str] = []
        checks = await self._get_related_checks()

        if additional_checks:
            checks.extend(additional_checks)

        for attr_name, model, filter_field in checks:
            value = getattr(data, attr_name, None)
            if value is not None and value:
                if not await self._check_object_exists(
                    model, **{filter_field: value}
                ):
                    errors.append(
                        f"{model.__name__} with {filter_field}={value} "
                        "not found"
                    )

        if errors:
            logger.exception(f"Related objects not found: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related objects not found: {errors}",
            )

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        return self._default_related_create

    async def _create_or_update_related(
        self,
        data: SchemaTypeCreate | SchemaTypeUpdate,
        additional_checks: Optional[dict[str, tuple[Any, Any, bool]]] = None,
    ) -> None:
        from ..dependencies import get_exists_cache, get_updated_cache

        errors: list[str] = []
        checks = await self._get_related_create()
        # Для отслеживания уже обработанных сущностей
        processed_entities: set[Any] = set()
        updated_cache = get_updated_cache()
        if additional_checks:
            checks.update(additional_checks)
        for field_name, (client, model, required) in checks.items():
            value = getattr(data, field_name, None)

            if not value:
                if required:
                    errors.append(f"Missing required field: {field_name}")
                continue

            try:
                # Ключ для отслеживания уже обработанных сущностей
                entity_key = (model, value)

                # Пропускаем, если уже обрабатывали эту сущность
                if entity_key in processed_entities | updated_cache:
                    continue

                # Добавляем в отслеживаемые
                processed_entities.add(entity_key)

                # Формируем ключ кэша для проверки существования
                filters = {"external_id": value}
                sorted_filters = tuple(sorted(filters.items()))
                cache_key = (model, sorted_filters)

                if not await self._check_object_exists(
                    model, external_id=value
                ):
                    await client.import_from_bitrix(value)
                    cache = get_exists_cache()
                    if cache_key in cache:
                        del cache[cache_key]
                else:
                    # print(f"{value} :: {client} ----")
                    await client.refresh_from_bitrix(value)
                    updated_cache.add(entity_key)
                    # print(f"{value} :: {client} ++++")
            except Exception as e:
                errors.append(
                    f"{model.__name__} with id={value} failed: {str(e)}"
                )

        if errors:
            logger.exception(f"Related objects processing failed: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=", ".join(errors),
            )
