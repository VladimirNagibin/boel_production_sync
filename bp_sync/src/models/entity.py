from datetime import datetime
from enum import StrEnum

from sqlalchemy import (  # , Column, Integer, String
    CheckConstraint,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base


class DealType(Base):
    """
    Тип сделки:
    1 - Продажа BOEL
    3 - Продажа Колонны
    5 - Интернет продажа
    4 - BOEL Engineering
    SALE - Гарантийное обслуживание
    6 - Сервис
    7 - ВЭД
    UC_76MJ0I - Входящие
    UC_FSOZEI - Исходящие
    """

    __tablename__ = "deal_types"
    type_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="type")


class DealStage(Base):
    """
    Стадия:
    NEW - Не разобрано
    PREPAYMENT_INVOICE - Выявление потребности
    PREPARATION - Заинтересован
    EXECUTING - Согласование условий договор
    FINAL_INVOICE - Выставление счёта
    1 - На отгрузку
    WON - Выиграна
    LOSE - Проиграна
    APOLOGY - Анализ проигрыша
    """

    __tablename__ = "deal_stages"
    stage_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    order: Mapped[int] = mapped_column(unique=True)  # порядковый номер
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="stage")


class Currency(Base):
    """
    Валюта:
    ID    name              cource~ nominal
    RUB - Российский рубль  1       1
    USD - Доллар США        78.4839 1
    EUR - Евро              89.8380 1
    UAH - Гривна            18.8277 10
    BYN - Белорусский рубль 26,3696 1
    KZT - Тенге             15.1277 100
    """

    __tablename__ = "currencies"
    currency_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    cource: Mapped[float]
    nominal: Mapped[int]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="currency"
    )


class Lead(Base):
    """
    Лиды
    """

    __tablename__ = "leads"
    lead_id: Mapped[int] = mapped_column(unique=True)
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="lead")


class Company(Base):
    """
    Компании
    """

    __tablename__ = "companies"
    company_id: Mapped[int] = mapped_column(unique=True)
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="company"
    )


class Contact(Base):
    """
    Контакты
    """

    __tablename__ = "contacts"
    contact_id: Mapped[int] = mapped_column(unique=True)
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="contact"
    )


class User(Base):
    """
    Пользователи
    """

    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
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


class Category(Base):
    """
    Направления сделок (воронки):
    0 - общее направление
    1 - сервис
    2 - отгрузка со склада
    """

    __tablename__ = "categories"
    category_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="category"
    )


class StageSemanticEnum(StrEnum):
    """
    Статусы стадии сделки:
    P - В работе
    S - Успешная
    F - Провал
    """

    IN_PROCESS = "P"
    SUCCESS = "S"
    FAIL = "F"


class Source(Base):
    """
    Источники сделок:
    PARTNER : Существующий клиент
    19 : Новый клиент
    20 : Шоурум
    21 : Интернет
    """

    __tablename__ = "sources"
    source_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="source")


class MainActivity(Base):
    """
    Основная деятельность клиента:
    147: Дистрибьютор
    149: Домашний пивовар
    151: Завод
    153: Крафт
    155: Наш дилер
    157: Розница
    159: Сети
    161: Торговая компания
    163: Хорека
    """

    __tablename__ = "main_activites"
    main_activity_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="main_activity"
    )


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
        CheckConstraint(
            "probability IS NULL OR (probability BETWEEN 0 AND 100)",
            name="valid_probability_range",
        ),
        CheckConstraint("deal_id > 0", name="deal_id_positive"),
    )
    deal_id: Mapped[int] = mapped_column(unique=True)  # ID : ид
    title: Mapped[str]  # TITLE : Название
    type_id: Mapped[str] = mapped_column(
        ForeignKey("deal_types.type_id")
    )  # TYPE_ID : Тип сделки
    type: Mapped["DealType"] = relationship("DealType", back_populates="deals")
    stage_id: Mapped[str] = mapped_column(
        ForeignKey("deal_stages.stage_id")
    )  # STAGE_ID : Идентификатор стадии сделки
    stage: Mapped["DealStage"] = relationship(
        "DealStage", back_populates="deals"
    )
    probability: Mapped[int | None]  # PROBABILITY : Вероятность
    currency_id: Mapped[str] = mapped_column(
        ForeignKey("currencies.currency_id")
    )  # CURRENCY_ID : Ид валюты
    currency: Mapped["Currency"] = relationship(
        "Currency", back_populates="deals"
    )
    opportunity: Mapped[float]  # OPPORTUNITY : Сумма
    is_manual_opportunity: Mapped[bool]
    # IS_MANUAL_OPPORTUNITY : Сумма заполнена вручную
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.lead_id")
    )  # LEAD_ID : Ид лида
    lead: Mapped["Lead"] = relationship("Lead", back_populates="deals")
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.company_id")
    )  # COMPANY_ID : Ид компании
    company: Mapped["Company"] = relationship(
        "Company", back_populates="deals"
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.contact_id")
    )  # CONTACT_ID : Ид контакта
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="deals"
    )
    begindate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # BEGINDATE : Дата начала (2025-06-18T03:00:00+03:00)
    closedate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # CLOSEDATE : Дата завершения
    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # ASSIGNED_BY_ID : Ид пользователя
    assigned_user: Mapped["User"] = relationship(
        "User", back_populates="assigned_deals"
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # CREATED_BY_ID : Ид пользователя
    created_user: Mapped["User"] = relationship(
        "User", back_populates="created_deals"
    )
    modify_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # MODIFY_BY_ID : Ид пользователя
    modify_user: Mapped["User"] = relationship(
        "User", back_populates="modify_deals"
    )
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # DATE_CREATE : Дата создания
    date_modify: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # DATE_MODIFY : Дата изменения
    opened: Mapped[bool]  # OPENED : Доступен для всех (Y/N)
    closed: Mapped[bool]  # CLOSET : Завершена ли сделка (Y/N)
    comments: Mapped[str | None]  # COMMENTS : Коментарии
    additional_info: Mapped[str | None]
    #  ADDITIONAL_INFO : Дополнительная информация
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id")
    )  # CATEGORY_ID : Идентификатор направления
    category: Mapped["Category"] = relationship(
        "Category", back_populates="deals"
    )
    stage_semantic_id: Mapped[str] = mapped_column(
        PgEnum(
            StageSemanticEnum,
            name="deal_stage_enum",
            create_type=False,
            default=0,
            server_default="NOT_DEFINED",
        )
    )
    is_new: Mapped[bool]  # IS_NEW : Флаг новой сделки (Y/N)
    is_recurring: Mapped[bool]
    # IS_RECURRING : Флаг шаблона регулярной сделки.
    # Если стоит Y, то это шаблон, а не сделка (Y/N)
    is_return_customer: Mapped[bool]
    # IS_RETURN_CUSTOMER : Признак повторного лида (Y/N)
    is_repeated_approach: Mapped[bool]
    # IS_REPEATED_APPROACH : Повторное обращение (Y/N)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.source_id")
    )  # SOURCE_ID : Идентификатор источника (сводно)
    source: Mapped["Source"] = relationship("Source", back_populates="deals")
    source_description: Mapped[str | None]
    # SOURCE_DESCRIPTION : Дополнительно об источнике
    originator_id: Mapped[str | None]
    # ORIGINATOR_ID : Идентификатор источника данных
    origin_id: Mapped[str | None]
    # ORIGIN_ID : Идентификатор элемента в источнике данных
    moved_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", back_populates="moved_deals"
    )
    moved_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # MOVED_TIME : Дата перемещения элемента на текущую стадию
    last_activity_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # LAST_ACTIVITY_TIME : Время последней активности
    last_communication_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )  # LAST_COMMUNICATION_TIME : Дата ???
    last_activity_by: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # LAST_ACTIVITY_BY : Ид пользователя сделавшего крайнюю за активность
    last_activity_user: Mapped["User"] = relationship(
        "User", back_populates="last_activity_deals"
    )
    main_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("main_activites.main_activity_id")
    )  # UF_CRM_1598883361 : Ид основной деятельности клиента
    main_activity: Mapped["MainActivity"] = relationship(
        "MainActivity", back_populates="deals"
    )
    city: Mapped[str | None]  # UF_CRM_DCT_CITY : Город (населённый пункт)
    source_external: Mapped[str | None]  # UF_CRM_DCT_SOURCE : Источник внешний
