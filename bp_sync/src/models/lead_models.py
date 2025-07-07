from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import CommunicationIntIdEntity, EntityType
from .entities import Company, Contact, User
from .enums import StageSemanticEnum
from .references import (
    Currency,
    DealFailureReason,
    DealType,
    LeadStatus,
    MainActivity,
    Source,
)

if TYPE_CHECKING:
    from .deal_models import Deal


class Lead(CommunicationIntIdEntity):
    """
    Лиды
    """

    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
    )

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название лида"
    )  # TITLE : Название
    comments: Mapped[str | None] = mapped_column(
        comment="Комментарии"
    )  # COMMENTS : Коментарии
    name: Mapped[str | None] = mapped_column(
        comment="Имя контакта"
    )  # NAME : Имя контакта
    second_name: Mapped[str | None] = mapped_column(
        comment="Отчество контакта"
    )  # SECOND_NAME : Отчество контакта
    last_name: Mapped[str | None] = mapped_column(
        comment="Фамилия контакта"
    )  # LAST_NAME : Фамилия контакта
    post: Mapped[str | None] = mapped_column(
        comment="Должность"
    )  # POST : Должность
    company_title: Mapped[str | None] = mapped_column(
        comment="Название компании, привязанной к лиду"
    )  # COMPANY_TITLE : Название компании, привязанной к лиду

    # Статусы и флаги
    is_manual_opportunity: Mapped[bool] = mapped_column(
        default=False, comment="Ручной ввод суммы"
    )  # IS_MANUAL_OPPORTUNITY : Сумма заполнена вручную
    opened: Mapped[bool] = mapped_column(
        default=True, comment="Доступна для всех"
    )  # OPENED : Доступен для всех (Y/N)
    is_return_customer: Mapped[bool] = mapped_column(
        default=False, comment="Повторный клиент"
    )  # IS_RETURN_CUSTOMER : Признак повторного лида (Y/N)
    is_shipment_approved: Mapped[bool | None] = mapped_column(
        comment="Разрешение на отгрузку"
    )  # UF_CRM_1623830089 : Разрешение на отгрузку (1/0)
    has_phone: Mapped[bool] = mapped_column(
        default=False, comment="Признак заполненности поля телефон"
    )  # HAS_PHONE : Признак заполненности поля телефон (Y/N)
    has_email: Mapped[bool] = mapped_column(
        default=False, comment="Признак заполненности электронной почты"
    )  # HAS_EMAIL : Признак заполненности поля электронной почты (Y/N)
    has_imol: Mapped[bool] = mapped_column(
        default=False, comment="Признак наличия привязанной открытой линии"
    )  # HAS_IMOL : Признак наличия привязанной открытой линии (Y/N)

    # Финансовые данные
    opportunity: Mapped[float] = mapped_column(
        default=0.0, comment="Сумма сделки"
    )  # OPPORTUNITY : Сумма

    # Временные метки
    birthdate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата рождения"
    )  # BIRTHDATE : Дата рождения (2025-06-18T03:00:00+03:00)
    date_closed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата закрытия"
    )  # DATE_CLOSED : Дата закрытия
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата создания"
    )  # DATE_CREATE : Дата создания
    date_modify: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата изменения"
    )  # DATE_MODIFY : Дата изменения
    moved_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата перемещения"
    )  # MOVED_TIME : Дата перемещения элемента на текущую стадию
    last_activity_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Время последней активности"
    )  # LAST_ACTIVITY_TIME : Время последней активности
    last_communication_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), comment="Время последней коммуникации"
    )  # LAST_COMMUNICATION_TIME : Дата 02.02.2024  15:21:08

    # География и источники
    city: Mapped[str | None] = mapped_column(
        comment="Город (населённый пункт)"
    )  # UF_CRM_DCT_CITY : Город (населённый пункт)
    source_description: Mapped[str | None] = mapped_column(
        comment="Описание источника"
    )  # SOURCE_DESCRIPTION : Описание источника
    status_description: Mapped[str | None] = mapped_column(
        comment="Дополнительно о стадии"
    )  # STATUS_DESCRIPTION : Дополнительно о стадии
    source_external: Mapped[str | None] = mapped_column(
        comment="Внешний источник"
    )  # UF_CRM_DCT_SOURCE : Источник внешний
    originator_id: Mapped[str | None] = mapped_column(
        comment="ID источника данных"
    )  # ORIGINATOR_ID : Идентификатор источника данных
    origin_id: Mapped[str | None] = mapped_column(
        comment="ID элемента в источнике"
    )  # ORIGIN_ID : Идентификатор элемента в источнике данных

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

    # Перечисляемые типы
    status_semantic_id: Mapped[StageSemanticEnum] = mapped_column(
        PgEnum(
            StageSemanticEnum,
            name="deal_stage_enum",
            create_type=False,
            default=StageSemanticEnum.PROSPECTIVE,
            server_default=StageSemanticEnum.PROSPECTIVE.value,
        ),
        comment="Семантика стадии",
    )  # STATUS_SEMANTIC_ID : Статусы стадии лида
    # processing_status: Mapped[ProcessingStatusEnum] = mapped_column(
    #    PgEnum(
    #        ProcessingStatusEnum,
    #        name="processing_status_enum",
    #        create_type=False,
    #        default=ProcessingStatusEnum.NOT_DEFINE,
    #        server_default=0,
    #    ),
    #    comment="Статус обработки",
    # )  # UF_CRM_1750571370 : Статус обработки

    # Связи с другими сущностями
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="lead")
    currency_id: Mapped[str | None] = mapped_column(
        ForeignKey("currencies.external_id")
    )  # CURRENCY_ID : Ид валюты
    currency: Mapped["Currency"] = relationship(
        "Currency", back_populates="leads"
    )
    type_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_types.external_id")
    )  # UF_CRM_1629271075 : Тип лида
    type: Mapped["DealType"] = relationship("DealType", back_populates="leads")
    status_id: Mapped[str] = mapped_column(
        ForeignKey("lead_statuses.external_id")
    )  # STATUS_ID : Идентификатор стадии лида
    status: Mapped["LeadStatus"] = relationship(
        "LeadStatus", back_populates="leads"
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id")
    )  # COMPANY_ID : Ид компании
    company: Mapped["Company"] = relationship(
        "Company", back_populates="leads"
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.external_id")
    )  # CONTACT_ID : Ид контакта
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="leads"
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.external_id")
    )  # SOURCE_ID : Идентификатор источника (сводно)
    source: Mapped["Source"] = relationship("Source", back_populates="leads")
    main_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("main_activites.ext_alt_id")
    )  # UF_CRM_1598882174 : Ид основной деятельности клиента
    main_activity: Mapped["MainActivity"] = relationship(
        "MainActivity", back_populates="leads"
    )
    deal_failure_reason_id: Mapped[int | None] = mapped_column(
        ForeignKey("deal_failure_reasons.ext_alt_id")
    )  # UF_CRM_1697036607 : Ид причины провала
    deal_failure_reason: Mapped["DealFailureReason"] = relationship(
        "DealFailureReason", back_populates="leads"
    )

    # Пользователи
    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID ответственного",
    )  # ASSIGNED_BY_ID : Ид пользователя
    assigned_user: Mapped["User"] = relationship(
        "User", foreign_keys=[assigned_by_id], back_populates="assigned_leads"
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID создателя",
    )  # CREATED_BY_ID : Ид пользователя
    created_user: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by_id], back_populates="created_leads"
    )
    modify_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID изменившего",
    )  # MODIFY_BY_ID : Ид пользователя
    modify_user: Mapped["User"] = relationship(
        "User", foreign_keys=[modify_by_id], back_populates="modify_leads"
    )
    moved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID переместившего",
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", foreign_keys=[moved_by_id], back_populates="moved_leads"
    )
    last_activity_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID последней активности",
    )  # LAST_ACTIVITY_BY : Ид пользователя сделавшего крайнюю за активность
    last_activity_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[last_activity_by],
        back_populates="last_activity_leads",
    )

    # Маркетинговые метки
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
    )  # UF_CRM_CALLTOUCHT413 : ID сайта в Calltouch
    calltouch_call_id: Mapped[str | None] = mapped_column(
        comment="ID звонка в Calltouch"
    )  # UF_CRM_CALLTOUCH3ZFT : ID звонка в Calltouch
    calltouch_request_id: Mapped[str | None] = mapped_column(
        comment="ID заявки в Calltouch"
    )  # UF_CRM_CALLTOUCHWG9P : ID заявки в Calltouch
    yaclientid: Mapped[str | None] = mapped_column(
        comment="yaclientid"
    )  # UF_CRM_1739432591418 : yaclientid

    # Социальные профили
    wz_instagram: Mapped[str | None] = mapped_column(
        comment="Instagram"
    )  # UF_CRM_INSTAGRAM_WZ : Instagram
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
    """ remaining fields:
    "HONORIFIC": str, Вид обращения. Статус из справочника.

    "UF_CRM_1598882341": str, Промывочная жидкость клиента
    "UF_CRM_1598882312": list, Пеногасители клиента

    "UF_CRM_ZOOM_MEET_LINK": str, Ссылка на Zoom
    "UF_CRM_ZOOM_MEET_TZ": str, Дата/время Zoom

    "UF_CRM_DCT_UID": ДКТ: client_id
    "UF_CRM_DCT_CID": ДКТ: client_cid
    "UF_CRM_DCT_YA_CID": ДКТ: ya_client_id
    "UF_CRM_DCT_MEDIUM": ДКТ: Канал
    "UF_CRM_DCT_CAMPAIGN": ДКТ: Кампания
    "UF_CRM_DCT_CONTENT": ДКТ: Содержимое
    "UF_CRM_DCT_TERM": ДКТ: Что искал
    "UF_CRM_DCT_DURATION": ДКТ: Время на сайте
    "UF_CRM_DCT_PAGE": ДКТ: Страница звонка
    "UF_CRM_DCT_CONTEXT": ДКТ: Контекст вызова
    "UF_CRM_DCT_CUSTOM": ДКТ: Custom
    "UF_CRM_DCT_WID_NAME": ДКТ: Имя виджета
    "UF_CRM_DCT_TYPE": ДКТ: Тип заявки
    "UF_CRM_DCT_SID": ДКТ: client_sid

    "UF_CRM_ROISTAT": riostat
    """

    @property
    def entity_type(self) -> EntityType:
        return EntityType.LEAD
