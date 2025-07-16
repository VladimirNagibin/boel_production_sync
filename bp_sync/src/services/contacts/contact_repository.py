from typing import Type

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base, get_session
from models.bases import EntityType
from models.company_models import Company
from models.contact_models import Contact as ContactDB
from models.references import (
    ContactType,
    DealFailureReason,
    DealType,
    MainActivity,
    Source,
)
from schemas.contact_schemas import ContactCreate, ContactUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)


class ContactRepository(
    EntityWithCommunicationsRepository[ContactDB, ContactCreate, ContactUpdate]
):

    model = ContactDB
    entity_type = EntityType.CONTACT

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_entity(self, data: ContactCreate) -> ContactDB:
        """Создает новый контакт с проверкой связанных объектов"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: ContactCreate | ContactUpdate
    ) -> ContactDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(data=data)

    def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("type_id", ContactType, "external_id"),
            ("source_id", Source, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt2_id"),
            ("deal_failure_reason_id", DealFailureReason, "ext_alt2_id"),
            (" deal_type_id", DealType, "external_id"),
        ]

    async def _create_or_update_related(
        self, lead_schema: ContactCreate | ContactUpdate
    ) -> None:
        """
        Проверяет существование всех связанных объектов в БД и
        создаёт при отсутствии
        """
        errors: list[str] = []

        # Проверка company
        if company_id := lead_schema.company_id:
            if not await self._check_object_exists(
                Company, external_id=company_id
            ):
                errors.append(f"Company with id={company_id:} not found")

        """
        # Проверка Contact
        if not await check_object_exists(
            db, Company, company_id=deal_data["company_id"]
        ):
            errors.append(
                f"Company with company_id={deal_data['company_id']} not found"
            )

        # Проверка User для assigned_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["assigned_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['assigned_by_id']} not found"
            )

        # Проверка User для created_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["created_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['created_by_id']} not found"
            )

        # Проверка User для modify_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["modify_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['modify_by_id']} not found"
            )

        # Проверка User для moved_by_id
        if not await check_object_exists(
            db, User, user_id=deal_data["moved_by_id"]
        ):
            errors.append(
                f"User with user_id={deal_data['moved_by_id']} not found"
            )

        # Проверка User для last_activity_by
        if not await check_object_exists(
            db, User, user_id=deal_data["last_activity_by"]
        ):
            errors.append(
                f"User with user_id={deal_data['last_activity_by']} not found"
            )
        """
        if errors:
            logger.exception(f"Failed to create related objects: {errors}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to create related objects: {errors}",
            )


def get_contact_repository(
    session: AsyncSession = Depends(get_session),
) -> ContactRepository:
    return ContactRepository(session)
