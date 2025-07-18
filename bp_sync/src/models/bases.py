from datetime import datetime
from enum import StrEnum, auto
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base

if TYPE_CHECKING:
    from .communications import CommunicationChannel
    from .user_models import User


class EntityType(StrEnum):
    CONTACT = "Contact"
    COMPANY = "Company"
    LEAD = "Lead"
    DEAL = "Deal"
    USER = "User"
    INVOICE = "Invoice"


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


class TimestampsMixin:
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата создания"
    )  # DATE_CREATE : Дата создания  (2025-06-18T03:00:00+03:00)
    date_modify: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата изменения"
    )  # DATE_MODIFY : Дата изменения
    last_activity_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Время последней активности"
    )  # LAST_ACTIVITY_TIME : Время последней активности
    last_communication_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), comment="Время последней коммуникации"
    )  # LAST_COMMUNICATION_TIME : Дата 02.02.2024  15:21:08


class UserRelationsMixin:
    """Миксин для отношений с пользователями"""

    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID ответственного",
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID создателя",
    )
    modify_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID изменившего",
    )
    last_activity_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID последней активности",
    )

    @property
    def tablename(self) -> str:
        raise NotImplementedError("Должно быть реализовано в дочернем классе")

    @property
    def entity_type(self) -> EntityType:
        raise NotImplementedError("Должно быть реализовано в дочернем классе")

    @declared_attr  # type: ignore[misc]
    def assigned_user(cls) -> Mapped["User"]:
        return relationship(
            "User",
            foreign_keys=f"{cls.entity_type}.assigned_by_id",
            back_populates=f"assigned_{cls.tablename}",
        )

    @declared_attr  # type: ignore[misc]
    def created_user(cls) -> Mapped["User"]:
        return relationship(
            "User",
            foreign_keys=f"{cls.entity_type}.created_by_id",
            back_populates=f"created_{cls.tablename}",
        )

    @declared_attr  # type: ignore[misc]
    def modify_user(cls) -> Mapped["User"]:
        return relationship(
            "User",
            foreign_keys=f"{cls.entity_type}.modify_by_id",
            back_populates=f"modify_{cls.tablename}",
        )

    @declared_attr  # type: ignore[misc]
    def last_activity_user(cls) -> Mapped["User"]:
        return relationship(
            "User",
            foreign_keys=f"{cls.entity_type}.last_activity_by",
            back_populates=f"last_activity_{cls.tablename}",
        )


class MarketingMixinUTM:
    utm_source: Mapped[str | None] = mapped_column(
        comment="Рекламная система"
    )  # UTM_SOURCE : Рекламная система (Yandex-Direct, Google-Adwords и др)
    utm_medium: Mapped[str | None] = mapped_column(
        comment="Тип трафика"
    )  # UTM_MEDIUM : Тип трафика: CPC (объявления), CPM (баннеры)
    utm_campaign: Mapped[str | None] = mapped_column(
        comment="Обозначение рекламной кампании"
    )  # UTM_CAMPAIGN : Обозначение рекламной кампании
    utm_content: Mapped[str | None] = mapped_column(
        comment="Содержание кампании"
    )  # UTM_CONTENT : Содержание кампании. Например, для контекстных
    # объявлений
    utm_term: Mapped[str | None] = mapped_column(
        comment="Тип трафика"
    )  # UTM_TERM : Условие поиска кампании. Например, ключевые слова
    # контекстной рекламы


class MarketingMixin:
    mgo_cc_entry_id: Mapped[str | None] = mapped_column(
        comment="ID звонка"
    )  # UF_CRM_MGO_CC_ENTRY_ID : ID звонка
    mgo_cc_channel_type: Mapped[str | None] = mapped_column(
        comment="Канал обращения"
    )  # UF_CRM_MGO_CC_CHANNEL_TYPE : Канал обращения
    mgo_cc_result: Mapped[str | None] = mapped_column(
        comment="Результат обращения"
    )  # UF_CRM_MGO_CC_RESULT : Результат обращения
    mgo_cc_entry_point: Mapped[str | None] = mapped_column(
        comment="Точка входа обращения"
    )  # UF_CRM_MGO_CC_ENTRY_POINT : Точка входа обращения
    mgo_cc_create: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата/время создания обращения"
    )  # UF_CRM_MGO_CC_CREATE : Дата/время создания обращения
    mgo_cc_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата/время завершения обращения"
    )  # UF_CRM_MGO_CC_END : Дата/время завершения обращения
    mgo_cc_tag_id: Mapped[str | None] = mapped_column(
        comment="Тематики обращения"
    )  # UF_CRM_MGO_CC_TAG_ID : Тематики обращения
    calltouch_site_id: Mapped[str | None] = mapped_column(
        comment="ID сайта в Calltouch"
    )  # - : ID сайта в Calltouch
    calltouch_call_id: Mapped[str | None] = mapped_column(
        comment="ID звонка в Calltouch"
    )  # - : ID звонка в Calltouch
    calltouch_request_id: Mapped[str | None] = mapped_column(
        comment="ID заявки в Calltouch"
    )  # - : ID заявки в Calltouch


class CommunicationMixin:
    """Миксин для автоматического получения телефонов, email и т.д."""

    has_phone: Mapped[bool] = mapped_column(
        default=False, comment="Признак заполненности поля телефон"
    )  # HAS_PHONE : Признак заполненности поля телефон (Y/N)
    has_email: Mapped[bool] = mapped_column(
        default=False, comment="Признак заполненности электронной почты"
    )  # HAS_EMAIL : Признак заполненности поля электронной почты (Y/N)
    has_imol: Mapped[bool] = mapped_column(
        default=False, comment="Признак наличия привязанной открытой линии"
    )  # HAS_IMOL : Признак наличия привязанной открытой линии (Y/N)

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

    @property
    def webs(self) -> list[str]:
        """Список сайтов"""
        return [
            c.value
            for c in self.communications
            if c.channel_type.type_id == CommunicationType.WEB
        ]

    @property
    def ims(self) -> list[str]:
        """Список мессенджеров"""
        return [
            c.value
            for c in self.communications
            if c.channel_type.type_id == CommunicationType.IM
        ]

    @property
    def links(self) -> list[str]:
        """Список ссылок"""
        return [
            c.value
            for c in self.communications
            if c.channel_type.type_id == CommunicationType.LINK
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


class SocialProfilesMixin:
    wz_instagram: Mapped[str | None] = mapped_column(
        comment="Instagram"
    )  # UF_CRM_INSTAGRAM_WZ : Instagram Лиды и Контакты
    wz_vc: Mapped[str | None] = mapped_column(
        comment="VC"
    )  # UF_CRM_VK_WZ : VC
    wz_telegram_username: Mapped[str | None] = mapped_column(
        comment="Telegram username"
    )  # UF_CRM_TELEGRAMUSERNAME_WZ : Telegram username
    wz_telegram_id: Mapped[str | None] = mapped_column(
        comment="Telegram Id"
    )  # UF_CRM_TELEGRAMID_WZ : Telegram Id
    wz_avito: Mapped[str | None] = mapped_column(
        comment="Avito"
    )  # UF_CRM_AVITO_WZ : Avito


class AddressMixin:
    # Адрес
    address: Mapped[str | None] = mapped_column(
        comment="Адрес контакта"
    )  # ADDRESS : Адрес контакта
    address_2: Mapped[str | None] = mapped_column(
        comment="Вторая страница адреса"
    )  # ADDRESS_2 :  Вторая страница адреса. В некоторых странах принято
    # разбивать адрес на 2 части
    address_city: Mapped[str | None] = mapped_column(
        comment="Город"
    )  # ADDRESS_CITY : Город
    address_postal_code: Mapped[str | None] = mapped_column(
        comment="Почтовый индекс"
    )  # ADDRESS_POSTAL_CODE : Почтовый индекс
    address_region: Mapped[str | None] = mapped_column(
        comment="Район"
    )  # ADDRESS_REGION : Район
    address_province: Mapped[str | None] = mapped_column(
        comment="Область"
    )  # ADDRESS_PROVINCE : Область
    address_country: Mapped[str | None] = mapped_column(
        comment="Страна"
    )  # ADDRESS_COUNTRY : Страна
    address_country_code: Mapped[str | None] = mapped_column(
        comment="Код страны"
    )  # ADDRESS_COUNTRY_CODE : Код страны
    address_loc_addr_id: Mapped[int | None] = mapped_column(
        comment="Идентификатор адреса из модуля местоположений"
    )  # ADDRESS_LOC_ADDR_ID : Идентификатор адреса из модуля местоположений


class BusinessEntityCore(
    IntIdEntity,
    TimestampsMixin,
    UserRelationsMixin,
    MarketingMixin,
    SocialProfilesMixin,
):
    __abstract__ = True

    comments: Mapped[str | None] = mapped_column(
        comment="Комментарии"
    )  # COMMENTS : Коментарии
    source_description: Mapped[str | None] = mapped_column(
        comment="Описание источника"
    )  # SOURCE_DESCRIPTION : Дополнительно об источнике
    source_external: Mapped[str | None] = mapped_column(
        comment="Внешний источник"
    )  # UF_CRM_DCT_SOURCE : Источник внешний
    city: Mapped[str | None] = mapped_column(
        comment="Город"
    )  # UF_CRM_DCT_CITY : Город (населённый пункт)
    opened: Mapped[bool] = mapped_column(
        default=True, comment="Доступна для всех"
    )  # OPENED : Доступен для всех (Y/N)


class BusinessEntity(
    BusinessEntityCore,
    MarketingMixinUTM,
):
    __abstract__ = True

    originator_id: Mapped[str | None] = mapped_column(
        comment="ID источника данных"
    )  # ORIGINATOR_ID : Идентификатор источника данных
    origin_id: Mapped[str | None] = mapped_column(
        comment="ID элемента в источнике"
    )  # ORIGIN_ID : Идентификатор элемента в источнике данных


class CommunicationIntIdEntity(
    BusinessEntity, CommunicationMixin, AddressMixin
):
    """Базовая модель с внешним ID и коммуникациями"""

    __abstract__ = True
