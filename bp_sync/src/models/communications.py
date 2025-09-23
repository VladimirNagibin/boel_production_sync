from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

from .bases import CommunicationType, EntityType, IntIdEntity


class CommunicationChannelType(Base):
    __tablename__ = "communication_channel_types"
    __table_args__ = (
        UniqueConstraint(
            "type_id", "value_type", name="uq_channel_type_value_type"
        ),
    )
    type_id: Mapped[CommunicationType] = mapped_column(
        String(20),
        comment="Тип коммуникации",
    )  # TYPE_ID :  PHONE, EMAIL, WEB, IM, LINK
    value_type: Mapped[str] = mapped_column(
        String(50),
        comment="Уточнение типа коммуникации по каналу",
    )  # VALUE_TYPE :  WORK, HOME, MAIN, MOBILE и т.д.
    description: Mapped[str | None] = mapped_column(
        String(255),
        default=None,
        nullable=True,
    )
    channels: Mapped[list["CommunicationChannel"]] = relationship(
        "CommunicationChannel", back_populates="channel_type"
    )


class CommunicationChannel(IntIdEntity):
    __tablename__ = "communication_channels"
    # __table_args__ = (
    #    UniqueConstraint(
    #        "channel_type_id", "value", name="uq_channel_type_value"
    #    ),
    # )
    entity_type: Mapped[EntityType] = mapped_column(
        String(20),
        comment="Тип сущности",
        index=True,
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
        String(255), comment="Значение коннекта"
    )  # VALUE : Значение коннекта

    @hybrid_property  # type: ignore[misc]
    def type_id(self) -> str | None:
        return self.channel_type.type_id if self.channel_type else None

    @hybrid_property  # type: ignore[misc]
    def value_type(self) -> str | None:
        return self.channel_type.value_type if self.channel_type else None
