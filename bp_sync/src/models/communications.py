from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

from .bases import IntIdEntity


class CommunicationChannelType(Base):
    __tablename__ = "communication_channel_types"
    __table_args__ = (
        UniqueConstraint(
            "type_id", "value_type", name="uq_channel_type_value_type"
        ),
    )
    type_id: Mapped[str] = mapped_column(
        comment="Тип коммуникации"
    )  # TYPE_ID :  PHONE, EMAIL, WEB, IM, LINK
    value_type: Mapped[str] = mapped_column(
        comment="Уточнение типа коммуникации по каналу"
    )  # VALUE_TYPE :  WORK, HOME, MAIN, MOBILE и т.д.
    description: Mapped[str | None] = mapped_column(default=None)
    channels = relationship(
        "CommunicationChannel", back_populates="channel_type"
    )


class CommunicationChannel(IntIdEntity):
    __tablename__ = "communication_channels"
    entity_type: Mapped[str] = mapped_column(
        comment="Тип сущности"
    )  # lead, contact, company
    entity_id: Mapped[int] = mapped_column(
        comment="Внешний ID соответствующей сущности"
    )  # Внешний ID соответствующей сущности
    channel_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("communication_channel_types.id")
    )
    channel_type: Mapped["CommunicationChannelType"] = relationship(
        "CommunicationChannelType", back_populates="channels"
    )
    value: Mapped[str] = mapped_column(
        comment="Тип коммуникации"
    )  # VALUE : Значение коннекта
