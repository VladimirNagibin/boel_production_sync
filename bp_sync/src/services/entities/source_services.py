from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from models.references import Source as SourceDB
from schemas.source_schemas import Source


class SourceClient:

    model = SourceDB

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def import_from_bitrix(
        self, entity_id: str, entity_type_id: int | None = None
    ) -> SourceDB:
        """Импортирует сущность из Bitrix в базу данных"""
        logger.info(
            "Starting Source import from Bitrix",
            extra={"source_id": entity_id},
        )
        entity_data = Source(external_id=entity_id, name=entity_id)
        logger.debug(
            "Retrieved Source data from Bitrix",
            extra={
                "source_id": entity_id,
                "data": entity_data.model_dump(),
            },
        )
        try:
            obj = self.model(**entity_data.model_dump_db())
            self.session.add(obj)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(obj)
            logger.info(f"{self.model.__name__} created: ID={entity_id}")
            return obj
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(
                f"Integrity error creating {self.model.__name__} "
                f"ID={entity_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(f"Source with ID: {entity_id} already exists"),
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.exception(
                f"Database error creating {self.model.__name__} "
                f"ID={entity_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Database operation failed creating {self.model.__name__}"
                ),
            ) from e

    async def refresh_from_bitrix(
        self, entity_id: str, entity_type_id: int | None = None
    ) -> None:
        pass
