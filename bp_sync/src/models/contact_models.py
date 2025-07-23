from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey

# from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import CommunicationIntIdEntity, EntityType
from .references import (  # AdditionalResponsible,
    ContactType,
    DealFailureReason,
    DealType,
    MainActivity,
    Source,
)

if TYPE_CHECKING:
    from .company_models import Company
    from .deal_models import Deal
    from .invoice_models import Invoice
    from .lead_models import Lead


class Contact(CommunicationIntIdEntity):
    """
    Контакты
    """

    __tablename__ = "contacts"
    # __table_args__ = (
    #    CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
    # )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.CONTACT

    @property
    def entity_type1(self) -> str:
        return "Contact"

    @property
    def tablename(self) -> str:
        return self.__tablename__

    # Идентификаторы и основные данные
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
    origin_version: Mapped[str | None] = mapped_column(
        comment="Версия данных о контакте во внешней системе"
    )  # ORIGIN_VERSION : Версия данных о контакте во внешней системе

    # Статусы и флаги
    export: Mapped[bool] = mapped_column(
        default=False, comment="Участвует в экспорте контактов"
    )  # EXPORT : Участвует в экспорте контактов
    is_shipment_approved: Mapped[bool | None] = mapped_column(
        comment="Разрешение на отгрузку"
    )  # UF_CRM_60D97EF75E465 : Разрешение на отгрузку (1/0)

    # Временные метки
    birthdate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата рождения"
    )  # BIRTHDATE : Дата рождения (2025-06-18T03:00:00+03:00)

    # Связи с другими сущностями
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="contact", foreign_keys="[Deal.contact_id]"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="contact", foreign_keys="[Lead.contact_id]"
    )
    companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="contact",
        foreign_keys="[Company.contact_id]",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="contact",
        foreign_keys="[Invoice.contact_id]",
    )

    type_id: Mapped[str | None] = mapped_column(
        ForeignKey("contact_types.external_id")
    )  # TYPE_ID : Тип контакта
    type: Mapped["ContactType"] = relationship(
        "ContactType", back_populates="contacts"
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id")
    )  # COMPANY_ID : Ид компании
    company: Mapped["Company"] = relationship(
        "Company", back_populates="contacts", foreign_keys=[company_id]
    )
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.external_id")
    )  # LEAD_ID : Ид лида
    lead: Mapped["Lead"] = relationship(
        "Lead", back_populates="contacts", foreign_keys=[lead_id]
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.external_id")
    )  # SOURCE_ID : Идентификатор источника
    source: Mapped["Source"] = relationship(
        "Source", back_populates="contacts"
    )
    main_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("main_activites.ext_alt2_id")
    )  # UF_CRM_1598882745 : Ид основной деятельности клиента
    main_activity: Mapped["MainActivity"] = relationship(
        "MainActivity", back_populates="contacts"
    )
    deal_failure_reason_id: Mapped[int | None] = mapped_column(
        ForeignKey("deal_failure_reasons.ext_alt2_id")
    )  # UF_CRM_6539DA9518373 : Ид причины провала
    deal_failure_reason: Mapped["DealFailureReason"] = relationship(
        "DealFailureReason", back_populates="contacts"
    )
    deal_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_types.external_id")
    )  # UF_CRM_61236340EA7AC : Тип лида
    deal_type: Mapped["DealType"] = relationship(
        "DealType", back_populates="contacts"
    )

    """
    @declared_attr  # type: ignore[misc]
    def additional_responsables(cls) -> Mapped[list["AdditionalResponsible"]]:
        return relationship(
            "AdditionalResponsible",
            primaryjoin=(
                "and_("
                "foreign(AdditionalResponsible.entity_type) == "
                "cls.entity_type,"
                "foreign(AdditionalResponsible.entity_id) == cls.external_id)"
            ),
            viewonly=True,
            lazy="selectin",
            overlaps="communications",
        )  # UF_CRM_1629106625* : Доп ответственные
    """
    """ remaining fields:
    "HONORIFIC": str, Вид обращения. Статус из справочника.
    "PHOTO": file, Фотография
    "FACE_ID": int, Привязка к лицам из модуля faceid
    "COMPANY_IDS": Привязка контакта к компаниям. Множественное.

    "UF_CRM_1598883046": str, Промывочная жидкость клиента
    "UF_CRM_1598883025": list, Пеногасители клиента

    "UF_CRM_607CEFDD36007": str, Ссылка на Zoom
    "UF_CRM_607CEFDD44BA8": str, Дата/время Zoom

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
    "UF_CRM_6197548E9DD6D": ДКТ: Город (дубль)

    "UF_CRM_ROISTAT": riostat
    """
