from enum import StrEnum, auto
from typing import TYPE_CHECKING

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

if TYPE_CHECKING:
    from .communications import CommunicationChannel


class EntityType(StrEnum):
    CONTACT = "Contact"
    COMPANY = "Company"
    LEAD = "Lead"
    DEAL = "Deal"
    USER = "User"


class CommunicationType(StrEnum):
    PHONE = auto()
    EMAIL = auto()
    WEB = auto()
    IM = auto()
    LINK = auto()

    @staticmethod
    def has_value(value: str) -> bool:
        return value in CommunicationType.__members__


COMMUNICATION_TYPES = {
    "phone": CommunicationType.PHONE,
    "email": CommunicationType.EMAIL,
    "web": CommunicationType.WEB,
    "im": CommunicationType.IM,
    "link": CommunicationType.LINK,
}


class IntIdEntity(Base):
    """Базовый класс для сущностей с внешними ID"""

    __abstract__ = True
    external_id: Mapped[int] = mapped_column(
        unique=True,
        comment="ID во внешней системе",
    )


class NameIntIdEntity(IntIdEntity):
    """Базовый класс для сущностей с внешними ID и name"""

    __abstract__ = True
    name: Mapped[str]


class NameStrIdEntity(Base):
    """Базовый класс для сущностей со строчным внешними ID и name"""

    __abstract__ = True
    external_id: Mapped[str] = mapped_column(
        unique=True,
        comment="ID во внешней системе",
    )
    name: Mapped[str]


class CommunicationMixin:
    """Миксин для автоматического получения телефонов, email и т.д."""

    @declared_attr  # type: ignore[misc]
    def communications(cls) -> Mapped[list["CommunicationChannel"]]:
        return relationship(
            "CommunicationChannel",
            primaryjoin=(
                "and_("
                "foreign(CommunicationChannel.entity_type) == cls.entity_type,"
                "foreign(CommunicationChannel.entity_id) == cls.external_id)"
            ),
            viewonly=True,
            lazy="selectin",
            overlaps="communications",
        )

    @property
    def phones(self) -> list[str]:
        """Список телефонных номеров"""
        return [
            c.value
            for c in self.communications
            if c.channel_type.type_id == CommunicationType.PHONE
        ]

    @property
    def emails(self) -> list[str]:
        """Список email-адресов"""
        return [
            c.value
            for c in self.communications
            if c.channel_type.type_id == CommunicationType.EMAIL
        ]

    """
    @declared_attr
    def phones(self) -> Mapped[list["CommunicationChannel"]]:
        return relationship(
            "CommunicationChannel",
            primaryjoin=lambda: and_(
                foreign(CommunicationChannel.entity_type) == self.__name__,
                foreign(CommunicationChannel.entity_id) == self.external_id,
                foreign(CommunicationChannel.channel_type).has(type_id=CommunicationType.PHONE),
            ),
            viewonly=True,
            lazy="selectin",
        )

    @declared_attr
    def emails(self) -> Mapped[list["CommunicationChannel"]]:
        return relationship(
            "CommunicationChannel",
            primaryjoin=lambda: and_(
                foreign(CommunicationChannel.entity_type) == self.__qualname__,
                foreign(CommunicationChannel.entity_id) == self.external_id,
                foreign(CommunicationChannel.channel_type).has(type_id=CommunicationType.EMAIL),
            ),
            viewonly=True,
            lazy="selectin",
        )
    """


class CommunicationIntIdEntity(IntIdEntity, CommunicationMixin):
    """Базовая модель с внешним ID и коммуникациями"""

    __abstract__ = True

    @property
    def entity_type(self) -> EntityType:
        raise NotImplementedError("Должно быть реализовано в дочернем классе")
