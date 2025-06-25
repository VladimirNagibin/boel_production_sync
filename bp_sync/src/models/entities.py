from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from .bases import IntIdEntity, NameIntIdEntity

if TYPE_CHECKING:
    from .deal import Deal  # Типизация только при проверке типов


class Lead(IntIdEntity):
    """
    Лиды
    """

    __tablename__ = "leads"
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="lead")


class Contact(IntIdEntity):
    """
    Контакты
    """

    __tablename__ = "contacts"
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="contact"
    )


class Company(IntIdEntity):
    """
    Компании
    """

    __tablename__ = "companies"
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="company"
    )


class User(NameIntIdEntity):
    """
    Пользователи
    """

    __tablename__ = "users"
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
