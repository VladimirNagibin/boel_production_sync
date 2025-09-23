from typing import Any, Callable, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession

# from core.logger import logger
# from models.bases import EntityType
from models.timeline_comment_models import TimelineComment as TimelineCommDB
from models.user_models import User as UserDB
from schemas.timeline_comment_schemas import (
    TimelineCommentCreate,
    TimelineCommentUpdate,
)

from ..base_repositories.base_repository import BaseRepository
from ..users.user_services import UserClient


class TimelineCommentRepository(
    BaseRepository[
        TimelineCommDB, TimelineCommentCreate, TimelineCommentUpdate, int
    ]
):

    model = TimelineCommDB
    # entity_type = EntityType.LEAD

    def __init__(
        self,
        session: AsyncSession,
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
    ):
        super().__init__(session)
        self.get_user_client = get_user_client

    async def create_entity(
        self, data: TimelineCommentCreate
    ) -> TimelineCommDB:
        """Создает новый комментарий с проверкой связанных объектов"""
        await self._create_or_update_related(data)
        return await self.create(data=data)

    async def update_entity(
        self, data: TimelineCommentUpdate | TimelineCommentCreate
    ) -> TimelineCommDB:
        """Обновляет существующий лид"""
        await self._create_or_update_related(data)
        return await self.update(data=data)

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        user_client = await self.get_user_client()
        return {
            "author_id": (user_client, UserDB, True),
        }
