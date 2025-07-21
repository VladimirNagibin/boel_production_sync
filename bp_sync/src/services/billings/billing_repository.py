from typing import Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base, get_session
from models.deal_documents import Billing as BillingDB
from models.delivery_note_models import DeliveryNote as DeliveryNoteDB
from schemas.billing_schemas import BillingCreate, BillingUpdate

from ..base_repositories.base_repository import BaseRepository


class BillingRepository(
    BaseRepository[BillingDB, BillingCreate, BillingUpdate]
):

    model = BillingDB

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session)

    async def create_entity(self, data: BillingCreate) -> BillingDB:
        """Создает новый платёж с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: BillingCreate | BillingUpdate
    ) -> BillingDB:
        """Обновляет существующий платёж"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("delivery_note_id", DeliveryNoteDB, "external_id"),
        ]


def get_billing_repository(
    session: AsyncSession = Depends(get_session),
) -> BillingRepository:
    return BillingRepository(
        session=session,
    )
