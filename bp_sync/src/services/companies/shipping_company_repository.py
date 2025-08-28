from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from core.logger import logger
from models.references import ShippingCompany as ShippingCompanyDB
from schemas.company_schemas import (
    ShippingCompanyCreate,
    ShippingCompanyUpdate,
)

from ..base_repositories.base_repository import BaseRepository


class ShippingCompanyRepository(
    BaseRepository[
        ShippingCompanyDB, ShippingCompanyCreate, ShippingCompanyUpdate, int
    ]
):

    model = ShippingCompanyDB

    async def get_external_id_by_name(self, name: str) -> int | None:
        """
        Получить external_id компании отгрузки по названию

        Args:
            name: Название компании отгрузки

        Returns:
            external_id компании или None, если не найдена
        """
        try:
            stmt = select(ShippingCompanyDB.external_id).where(
                ShippingCompanyDB.name == name
            )
            result = await self.session.execute(stmt)
            external_id = result.scalar_one_or_none()
            return external_id  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при поиске компании по названию '{name}': {e}"
            )
            raise RuntimeError(
                f"Не удалось найти компанию по названию: {name}"
            ) from e

    async def get_external_id_by_ext_alt_id(
        self, ext_alt_id: int
    ) -> int | None:
        """
        Получить external_id компании отгрузки по ext_alt_id

        Args:
            ext_alt_id: Альтернативный ID компании отгрузки

        Returns:
            external_id компании или None, если не найдена
        """
        try:
            stmt = select(ShippingCompanyDB.external_id).where(
                ShippingCompanyDB.ext_alt_id == ext_alt_id
            )
            result = await self.session.execute(stmt)
            external_id = result.scalar_one_or_none()
            return external_id  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при поиске компании по ext_alt_id '{ext_alt_id}': {e}"
            )
            raise RuntimeError(
                f"Не удалось найти компанию по ext_alt_id: {ext_alt_id}"
            ) from e
