from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

if TYPE_CHECKING:
    from .entities import User  # Типизация только при проверке типов


class IntIdEntity(Base):
    """Базовый класс для сущностей с внешними ID"""

    __abstract__ = True
    external_id: Mapped[int] = mapped_column(unique=True)


class NameIntIdEntity(IntIdEntity):
    """Базовый класс для сущностей с внешними ID и name"""

    __abstract__ = True
    name: Mapped[str]


class NameStrIdEntity(Base):
    """Базовый класс для сущностей со строчным внешними ID и name"""

    __abstract__ = True
    external_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]


class UserRelationsMixin:
    """Миксин для отношений с пользователями"""

    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID ответственного",
    )  # ASSIGNED_BY_ID : Ид пользователя
    assigned_user: Mapped["User"] = relationship(
        "User", foreign_keys=[assigned_by_id], back_populates="assigned_deals"
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID создателя",
    )  # CREATED_BY_ID : Ид пользователя
    created_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by_id], back_populates="created_deals"
    )
    modify_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID изменившего",
    )  # MODIFY_BY_ID : Ид пользователя
    modify_user: Mapped["User"] = relationship(
        "User", foreign_keys=[modify_by_id], back_populates="modify_deals"
    )
    moved_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID переместившего",
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", foreign_keys=[moved_by_id], back_populates="moved_deals"
    )
    last_activity_by: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID последней активности",
    )  # LAST_ACTIVITY_BY : Ид пользователя сделавшего крайнюю за активность
    last_activity_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[last_activity_by],
        back_populates="last_activity_deals",
    )
    defect_expert_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID эксперта по дефектам",
    )  # UF_CRM_1655618547 : Ид эксперта по дефектам
    defect_expert: Mapped["User"] = relationship(
        "User", foreign_keys=[defect_expert_id], back_populates="defect_deals"
    )
