from fastapi import Depends, HTTPException, status
from sqlalchemy import delete, exists, select, update
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import get_session
from models.deal_models import Deal as DealDB
from schemas.deal_schemas import DealCreate, DealUpdate


class DealRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_deal(self, deal_schema: DealCreate) -> DealDB:
        """Создает новую сделку с проверкой на дубликаты"""
        external_id = deal_schema.external_id
        if await self._deal_exists(external_id):
            logger.warning(
                f"Deal creation conflict: ID={external_id} already exists"
            )
            raise self._deal_conflict_exception(external_id)

        try:
            new_deal = DealDB(**deal_schema.model_dump())
            self.session.add(new_deal)
            await self.session.commit()
            await self.session.refresh(new_deal)
            logger.info(f"Deal created successfully: ID={external_id}")
            return new_deal
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error creating deal ID={external_id}: {str(e)}"
            )
            raise self._deal_conflict_exception(deal_schema.external_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error creating deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create deal in database",
            ) from e

    async def get_deal_by_external_id(self, external_id: int) -> DealDB | None:
        """Возвращает сделку по external_id или None"""
        try:
            stmt = select(DealDB).where(DealDB.external_id == external_id)
            result = await self.session.execute(stmt)
            deal = result.scalar_one_or_none()
            if not deal:
                logger.debug(f"Deal not found: ID={external_id}")
            return deal  # type: ignore
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error fetching deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve deal from database",
            ) from e

    async def update_deal_by_external_id(
        self, deal_schema: DealUpdate
    ) -> DealDB:
        """Обновляет существующую сделку"""
        if not deal_schema.external_id:
            logger.error("Update failed: Missing deal ID")
            raise ValueError("Deal ID is required for update")
        update_data = deal_schema.model_dump(exclude_unset=True)
        external_id = deal_schema.external_id

        if not await self._deal_exists(external_id):
            logger.warning(f"Update failed: Deal ID={external_id} not found")
            raise self._deal_not_found_exception(external_id)

        # Оптимизированный запрос обновления
        stmt = (
            update(DealDB)
            .where(DealDB.external_id == external_id)
            .values(update_data)
            .returning(DealDB)
        )

        try:
            result = await self.session.execute(stmt)
            updated_deal = result.scalar_one()
            await self.session.commit()
            logger.info(f"Deal updated successfully: ID={external_id}")
            return updated_deal  # type: ignore
        except NoResultFound:
            await self.session.rollback()
            logger.warning(
                f"Update failed: Deal ID={external_id} not found after update"
            )
            raise self._deal_not_found_exception(external_id)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error updating deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update deal in database",
            ) from e

    async def delete_deal_by_external_id(self, external_id: int) -> bool:
        """Удаляет сделку по external_id, возвращает статус операции"""
        if not await self._deal_exists(external_id):
            logger.warning(f"Delete failed: Deal ID={external_id} not found")
            raise self._deal_not_found_exception(external_id)

        stmt = delete(DealDB).where(DealDB.external_id == external_id)
        try:
            result = await self.session.execute(stmt)
            await self.session.commit()

            if result.rowcount == 0:
                raise self._deal_not_found_exception(external_id)
            logger.info(f"Deal deleted successfully: ID={external_id}")
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error deleting deal ID={external_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete deal from database",
            ) from e

    async def _deal_exists(self, external_id: int) -> bool:
        """Проверяет существование сделки по external_id"""
        try:
            stmt = select(exists().where(DealDB.external_id == external_id))
            result = await self.session.execute(stmt)
            return bool(result.scalar())
        except SQLAlchemyError as e:
            logger.exception(
                "Database error checking deal existence "
                f"ID={external_id}: {str(e)}"
            )
            return False

    def _deal_not_found_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для отсутствующей сделки"""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with ID: {external_id} not found",
        )

    def _deal_conflict_exception(self, external_id: int) -> HTTPException:
        """Генерирует исключение для конфликта дубликатов"""
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Deal with ID: {external_id} already exists",
        )


def get_deal_repository(
    session: AsyncSession = Depends(get_session),
) -> DealRepository:
    return DealRepository(session)
