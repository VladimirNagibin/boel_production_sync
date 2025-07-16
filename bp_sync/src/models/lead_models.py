from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import CommunicationIntIdEntity, EntityType
from .enums import StageSemanticEnum
from .references import (
    Currency,
    DealFailureReason,
    DealType,
    LeadStatus,
    MainActivity,
    Source,
)
from .user_models import User

if TYPE_CHECKING:
    from .company_models import Company
    from .contact_models import Contact
    from .deal_models import Deal


class Lead(CommunicationIntIdEntity):
    """
    Лиды
    """

    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.LEAD

    @property
    def tablename(self) -> str:
        return self.__tablename__

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название лида"
    )  # TITLE : Название
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
    is_return_customer: Mapped[bool] = mapped_column(
        default=False, comment="Повторный клиент"
    )  # IS_RETURN_CUSTOMER : Признак повторного лида (Y/N)
    is_shipment_approved: Mapped[bool | None] = mapped_column(
        comment="Разрешение на отгрузку"
    )  # UF_CRM_1623830089 : Разрешение на отгрузку (1/0)

    # Финансовые данные
    opportunity: Mapped[float] = mapped_column(
        default=0.0, comment="Сумма сделки"
    )  # OPPORTUNITY : Сумма

    # Временные метки
    birthdate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата рождения"
    )  # BIRTHDATE : Дата рождения (2025-06-18T03:00:00+03:00)
    moved_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Время перемещения"
    )  # MOVED_TIME : Дата перемещения элемента на текущую стадию
    date_closed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата закрытия"
    )  # DATE_CLOSED : Дата закрытия

    # География и источники
    status_description: Mapped[str | None] = mapped_column(
        comment="Дополнительно о стадии"
    )  # STATUS_DESCRIPTION : Дополнительно о стадии

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
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="lead"
    )
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
    moved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID переместившего",
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", foreign_keys=[moved_by_id], back_populates="moved_leads"
    )

    # Маркетинговые метки
    yaclientid: Mapped[str | None] = mapped_column(
        comment="yaclientid"
    )  # UF_CRM_1739432591418 : yaclientid

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
