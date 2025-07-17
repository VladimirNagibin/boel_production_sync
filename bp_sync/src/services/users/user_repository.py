from typing import Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import Base, get_session
from models.bases import EntityType
from models.references import Department
from models.user_models import User as UserDB
from schemas.user_schemas import UserCreate, UserUpdate

from ..base_repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[UserDB, UserCreate, UserUpdate]):

    model = UserDB
    entity_type = EntityType.USER

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_entity(self, data: UserCreate) -> UserDB:
        """Создает нового пользователя с проверкой связанных объектов"""
        await self._check_related_objects(data)
        return await self.create(data=data)

    async def update_entity(self, data: UserCreate | UserUpdate) -> UserDB:
        """Обновляет существующего пользователя"""
        await self._check_related_objects(data)
        return await self.update(data=data)

    def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для User проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("department_id", Department, "external_id"),
        ]


def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)
