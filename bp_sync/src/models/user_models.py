from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base
from schemas.user_schemas import ManagerCreate, UserCreate

from .bases import EntityType, IntIdEntity
from .references import Department

if TYPE_CHECKING:
    from .company_models import Company
    from .contact_models import Contact
    from .deal_models import Deal
    from .delivery_note_models import DeliveryNote
    from .invoice_models import Invoice
    from .lead_models import Lead
    from .timeline_comment_models import TimelineComment


USERS_VALUES: list[tuple[int, bool, bool]] = [
    (171, True, False),
    (121, True, False),
    (29, True, False),
    (905, True, False),
    (923, True, False),
    (1039, True, False),
    (319, True, False),
    (1865, True, False),
    (3231, True, False),
    (5747, True, False),
    (9637, True, False),
    (5095, True, False),
    (11077, True, False),
    (227, True, False),
    (9023, True, False),
]


class User(IntIdEntity):
    """
    Пользователи
    """

    __tablename__ = "users"
    _schema_class = UserCreate

    @property
    def entity_type(self) -> EntityType:
        return EntityType.USER

    @property
    def entity_type1(self) -> str:
        return "User"

    @property
    def tablename(self) -> str:
        return self.__tablename__

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.last_name}"

    def __str__(self) -> str:
        return self.full_name

    # Идентификаторы и основные данные
    xml_id: Mapped[str | None] = mapped_column(
        comment="Внешний код"
    )  # XML_ID : Внешний код
    name: Mapped[str | None] = mapped_column(comment="Имя")  # NAME : Имя
    second_name: Mapped[str | None] = mapped_column(
        comment="Отчество"
    )  # SECOND_NAME : Отчество
    last_name: Mapped[str | None] = mapped_column(
        comment="Фамилия"
    )  # LAST_NAME : Фамилия
    personal_gender: Mapped[str | None] = mapped_column(
        comment="Пол"
    )  # PERSONAL_GENDER : Пол M / F
    work_position: Mapped[str | None] = mapped_column(
        comment="Должность"
    )  # WORK_POSITION : Должность
    user_type: Mapped[str | None] = mapped_column(
        comment="Тип пользователя"
    )  # USER_TYPE : Тип пользователя

    # Статусы и флаги
    active: Mapped[bool] = mapped_column(
        default=False, comment="Активность"
    )  # ACTIVE : Активность True / False
    is_online: Mapped[bool] = mapped_column(
        default=False, comment="Онлайн"
    )  # IS_ONLINE : Онлайн (Y/N)

    # Временные метки
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Последняя авторизация"
    )  # LAST_LOGIN : Последняя авторизация (2025-06-18T03:00:00+03:00)
    date_register: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата регистрации"
    )  # DATE_REGISTER : Дата регистрации
    personal_birthday: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата рождения"
    )  # PERSONAL_BIRTHDAY : Дата рождения
    employment_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Новая дата"
    )  # UF_EMPLOYMENT_DATE : Новая дата
    date_new: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Новая дата"
    )  # UF_USR_1699347879988 : Новая дата

    # География и источники
    time_zone: Mapped[str | None] = mapped_column(
        comment="Часовой пояс"
    )  # TIME_ZONE : Часовой пояс
    personal_city: Mapped[str | None] = mapped_column(
        comment="Город проживания"
    )  # PERSONAL_CITY : Город проживания

    # Коммуникации
    email: Mapped[str | None] = mapped_column(
        comment="E-Mail"
    )  # EMAIL : E-Mail
    personal_mobile: Mapped[str | None] = mapped_column(
        comment="Личный мобильный"
    )  # PERSONAL_MOBILE : Личный мобильный
    work_phone: Mapped[str | None] = mapped_column(
        comment="Телефон компании"
    )  # WORK_PHONE : Телефон компании
    personal_www: Mapped[str | None] = mapped_column(
        comment="Домашняя страничка"
    )  # PERSONAL_WWW : Домашняя страничка

    # Связи с другими сущностями
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.external_id")
    )  # UF_DEPARTMENT : отдел
    department: Mapped["Department"] = relationship(
        "Department", back_populates="users"
    )
    assigned_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="assigned_user",
        foreign_keys="[Deal.assigned_by_id]",
    )
    created_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="created_user",
        foreign_keys="[Deal.created_by_id]",
    )
    modify_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="modify_user",
        foreign_keys="[Deal.modify_by_id]",
    )
    moved_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="moved_user",
        foreign_keys="[Deal.moved_by_id]",
    )
    last_activity_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="last_activity_user",
        foreign_keys="[Deal.last_activity_by]",
    )
    defect_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="defect_expert",
        foreign_keys="[Deal.defect_expert_id]",
    )

    assigned_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="assigned_user",
        foreign_keys="[Lead.assigned_by_id]",
    )
    created_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="created_user",
        foreign_keys="[Lead.created_by_id]",
    )
    modify_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="modify_user",
        foreign_keys="[Lead.modify_by_id]",
    )
    moved_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="moved_user",
        foreign_keys="[Lead.moved_by_id]",
    )
    last_activity_leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="last_activity_user",
        foreign_keys="[Lead.last_activity_by]",
    )

    assigned_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="assigned_user",
        foreign_keys="[Contact.assigned_by_id]",
    )
    created_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="created_user",
        foreign_keys="[Contact.created_by_id]",
    )
    modify_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="modify_user",
        foreign_keys="[Contact.modify_by_id]",
    )
    last_activity_contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="last_activity_user",
        foreign_keys="[Contact.last_activity_by]",
    )

    assigned_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="assigned_user",
        foreign_keys="[Company.assigned_by_id]",
    )
    created_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="created_user",
        foreign_keys="[Company.created_by_id]",
    )
    modify_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="modify_user",
        foreign_keys="[Company.modify_by_id]",
    )
    last_activity_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="last_activity_user",
        foreign_keys="[Company.last_activity_by]",
    )

    assigned_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="assigned_user",
        foreign_keys="[Invoice.assigned_by_id]",
    )
    created_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="created_user",
        foreign_keys="[Invoice.created_by_id]",
    )
    modify_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="modify_user",
        foreign_keys="[Invoice.modify_by_id]",
    )
    moved_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="moved_user",
        foreign_keys="[Invoice.moved_by_id]",
    )
    last_activity_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="last_activity_user",
        foreign_keys="[Invoice.last_activity_by]",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="assigned_user",
        foreign_keys="[DeliveryNote.assigned_by_id]",
    )
    timeline_comments: Mapped[list["TimelineComment"]] = relationship(
        "TimelineComment",
        back_populates="author",
        foreign_keys="[TimelineComment.author_id]",
    )
    manager: Mapped["Manager"] = relationship(
        back_populates="user", uselist=False
    )


DEFAULT_COMPANY: list[tuple[int, str, float, bool]] = [
    (16079, "Company_16079", 0, False),
    (7925, "Company_7925", 0, False),
    (22095, "Company_22095", 0, False),
    (17709, "Company_17709", 0, False),
    (18453, "Company_18453", 0, False),
    (18845, "Company_18845", 0, False),
    (20631, "Company_20631", 0, False),
    (21063, "Company_21063", 0, False),
]

MANAGER_VALUES: list[tuple[int, bool, int | None, int | None]] = [
    (171, True, None, 19447),  # Admin
    (121, True, 16079, 19439),  # Ярославцева
    (29, True, 7925, 19419),  # Гузиков
    (905, True, 22095, 50427),  # Машаров
    (923, True, 17709, 53239),  # Михайлов
    (1039, True, 18453, 86617),  # Горбунов
    (319, True, 18845, 19469),  # Коротких
    (1865, True, 20631, 1),  # Ширяев
    (3231, True, 21063, 245681),  # Лукьянец
    (5747, True, None, 334643),  # Горбатько
    (9637, True, None, 449449),  # Ведешкин 23793
    (5095, True, None, 2),  # Internet
    (11077, True, None, 492127),  # Кулюхин 21859
    (227, True, None, 19451),  # Галанова
    (9023, True, None, 3),  # ВЭД
]


class Manager(Base):
    """
    Менеджеры
    """

    __tablename__ = "managers"
    _schema_class = ManagerCreate

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        unique=True,
        comment="ИД сотрудника",
    )
    user: Mapped["User"] = relationship("User", back_populates="manager")
    is_active: Mapped[bool] = mapped_column(
        default=False, comment="Менеджер активный"
    )
    default_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id")
    )
    default_company: Mapped["Company"] = relationship(
        "Company", back_populates="default_manager"
    )
    disk_id: Mapped[int | None] = mapped_column(comment="ИД диска")
