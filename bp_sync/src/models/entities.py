from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from .bases import CommunicationIntIdEntity, EntityType, NameIntIdEntity

if TYPE_CHECKING:
    from .deal_models import Deal
    from .lead_models import Lead


class Contact(CommunicationIntIdEntity):
    """
    Контакты
    """

    __tablename__ = "contacts"

    @property
    def entity_type(self) -> EntityType:
        return EntityType.CONTACT

    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="contact"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="contact"
    )


class Company(CommunicationIntIdEntity):
    """
    Компании
    """

    __tablename__ = "companies"

    @property
    def entity_type(self) -> EntityType:
        return EntityType.COMPANY

    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="company"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="company"
    )


class User(NameIntIdEntity):
    """
    Пользователи
    """

    __tablename__ = "users"

    @property
    def entity_type(self) -> EntityType:
        return EntityType.USER

    assigned_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="assigned_user"
    )
    created_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="created_user"
    )
    modify_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="modify_user"
    )
    moved_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="moved_user"
    )
    last_activity_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="last_activity_user"
    )
    defect_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="defect_expert"
    )
    assigned_leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="assigned_user"
    )
    created_leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="created_user"
    )
    modify_leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="modify_user"
    )
    moved_leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="moved_user"
    )
    last_activity_leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="last_activity_user"
    )
