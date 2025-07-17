from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import CommunicationIntIdEntity, EntityType
from .deal_documents import Contract
from .references import (
    AdditionalResponsible,
    ContactType,
    Currency,
    DealFailureReason,
    DealType,
    Emploees,
    Industry,
    MainActivity,
    ShippingCompany,
    Source,
)

if TYPE_CHECKING:
    from .contact_models import Contact
    from .deal_models import Deal
    from .lead_models import Lead


class Company(CommunicationIntIdEntity):
    """
    Компании
    """

    __tablename__ = "companies"
    # __table_args__ = (
    #    CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
    # )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.COMPANY

    @property
    def tablename(self) -> str:
        return self.__tablename__

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название сделки"
    )  # TITLE : Название
    origin_version: Mapped[str | None] = mapped_column(
        comment="Версия данных о контакте во внешней системе"
    )  # ORIGIN_VERSION : Версия данных о контакте во внешней системе

    # Финансы
    banking_details: Mapped[str | None] = mapped_column(
        comment="Банковские реквизиты"
    )  # BANKING_DETAILS : Банковские реквизиты
    revenue: Mapped[float] = mapped_column(
        default=0.0, comment="Годовой оборот"
    )  # REVENUE : Годовой оборот

    # Адреса
    address_legal: Mapped[str | None] = mapped_column(
        comment="Юридический адрес"
    )  # ADDRESS_LEGAL : Юридический адрес
    address_company: Mapped[str | None] = mapped_column(
        comment="Адрес (компания)"
    )  # UF_CRM_1596031539 : Адрес (компания)
    province_company: Mapped[str | None] = mapped_column(
        comment="Область (Край)"
    )  # UF_CRM_1596031556 : Область (Край)

    # Статусы и флаги
    is_my_company: Mapped[bool] = mapped_column(
        default=False, comment="Моя компания"
    )  # IS_MY_COMPANY : Моя компания
    is_shipment_approved: Mapped[bool | None] = mapped_column(
        comment="Разрешение на отгрузку"
    )  # UF_CRM_61974C16DBFBF : Разрешение на отгрузку (1/0)

    # Временные метки
    date_last_shipment: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата последней отгрузки"
    )  # UF_CRM_1623835088 : Дата последней отгрузки(2025-07-11T03:00:00+03:00)

    # Связи с другими сущностями
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="company"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="company"
    )
    contracts: Mapped[list["Contract"]] = relationship(
        "Contract", back_populates="company"
    )  # UF_CRM_1623833623*

    currency_id: Mapped[str | None] = mapped_column(
        ForeignKey("currencies.external_id")
    )  # CURRENCY_ID : Ид валюты
    currency: Mapped["Currency"] = relationship(
        "Currency", back_populates="deals"
    )
    company_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("contact_types.external_id")
    )  # COMPANY_TYPE : Тип контакта
    company_type: Mapped["ContactType"] = relationship(
        "ContactType", back_populates="companies"
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.external_id")
    )  # CONTACT_ID : Ид контакта
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="companies"
    )
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.external_id")
    )  # LEAD_ID : Ид лида
    lead: Mapped["Lead"] = relationship("Lead", back_populates="companies")
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.external_id")
    )  # UF_CRM_1637554945 : Идентификатор источника
    source: Mapped["Source"] = relationship(
        "Source", back_populates="companies"
    )
    main_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("main_activites.ext_alt3_id")
    )  # UF_CRM_1598882910 : Ид основной деятельности клиента
    main_activity: Mapped["MainActivity"] = relationship(
        "MainActivity", back_populates="companies"
    )
    deal_failure_reason_id: Mapped[int | None] = mapped_column(
        ForeignKey("deal_failure_reasons.ext_alt3_id")
    )  # UF_CRM_65A8D8C72059A : Ид причины провала
    deal_failure_reason: Mapped["DealFailureReason"] = relationship(
        "DealFailureReason", back_populates="companies"
    )
    deal_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_types.external_id")
    )  # UF_CRM_61974C16F0F71 : Тип лида
    deal_type: Mapped["DealType"] = relationship(
        "DealType", back_populates="companies"
    )
    shipping_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipping_companies.ext_alt_id")
    )  # UF_CRM_1631941968 : Ид текущей фирмы отгрузки
    shipping_company: Mapped["ShippingCompany"] = relationship(
        "ShippingCompany", back_populates="companies"
    )  # UF_CRM_1631903199* : Текущая фирма отгрузки
    industry_id: Mapped[str | None] = mapped_column(
        ForeignKey("industries.external_id")
    )  # INDUSTRY : Сфера деятельности
    industry: Mapped["Industry"] = relationship(
        "Industry", back_populates="companies"
    )
    employees_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.external_id")
    )  # EMPLOYEES : Численность сотрудников
    employees: Mapped["Emploees"] = relationship(
        "Employees", back_populates="companies"
    )

    parent_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id"), nullable=True
    )  # UF_CRM_1623833602 : Головная компания
    related_companies: Mapped[list["Company"]] = relationship(
        "Company",
        back_populates="parent_company",
        remote_side="[parent_company_id]",
    )  # Подчинённые компании
    parent_company: Mapped["Company | None"] = relationship(
        "Company",
        back_populates="related_companies",
        remote_side="[Company.external_id]",
        # foreign_keys="[Company.parent_company_id]",
    )  # Отношение к головной компании

    # Для договора
    position_head: Mapped[str | None] = mapped_column(
        comment="Должность руководителя"
    )  # UF_CRM_1630507939 : Должность руководителя
    basis_operates: Mapped[str | None] = mapped_column(
        comment="Основание деятельности предприятия"
    )  # UF_CRM_1630508048 : Основание деятельности предприятия
    position_head_genitive: Mapped[str | None] = mapped_column(
        comment="Должность руководителя родительный падеж"
    )  # UF_CRM_1632315102 : Должность руководителя родительный падеж
    basis_operates_genitive: Mapped[str | None] = mapped_column(
        comment="Основание деятельности предприятия родительный падеж"
    )  # UF_CRM_1632315157 : Основание деятельности предприятия
    # родительный падеж
    payment_delay_genitive: Mapped[str | None] = mapped_column(
        comment="Отсрочка родительный падеж"
    )  # UF_CRM_1632315337 : Отсрочка родительный падеж
    full_name_genitive: Mapped[str | None] = mapped_column(
        comment="ФИО родительный падеж"
    )  # UF_CRM_1633583719 : ФИО родительный падеж
    current_contract: Mapped[str | None] = mapped_column(
        comment="Текущий договор"
    )  # UF_CRM_1623915176 : Текущий договор
    current_number_contract: Mapped[str | None] = mapped_column(
        comment="Текущий номер договора"
    )  # UF_CRM_1654683828 : Текущий номер договора и код фирмы отгрузки
    # (для нового договора)

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
        )  # UF_CRM_1629106458* : Доп ответственные

    """ remaining fields:
    "LOGO": file, Логотип

    "REG_ADDRESS": Адрес компании. Устарел, используется для совместимости
    "REG_ADDRESS_2"
    "REG_ADDRESS_CITY"
    "REG_ADDRESS_POSTAL_CODE"
    "REG_ADDRESS_REGION"
    "REG_ADDRESS_PROVINCE"
    "REG_ADDRESS_COUNTRY"
    "REG_ADDRESS_COUNTRY_CODE"
    "REG_ADDRESS_LOC_ADDR_ID"

    "UF_CRM_1598883049": str, Промывочная жидкость клиента
    "UF_CRM_1598883027": list, Пеногасители клиента

    "UF_CRM_607968CD56A64": str, Ссылка на Zoom
    "UF_CRM_607968CD84FC5": str, Дата/время Zoom

    "UF_CRM_607968CDA31EE": ДКТ: client_id
    "UF_CRM_607968CDC27F7": ДКТ: client_cid
    "UF_CRM_607968CDE0017": ДКТ: ya_client_id
    "UF_CRM_607968CE1D781": ДКТ: Канал
    "UF_CRM_607968CE28037": ДКТ: Кампания
    "UF_CRM_607968CE39C33": ДКТ: Содержимое
    "UF_CRM_607968CE4B499": ДКТ: Что искал
    "UF_CRM_607968CE53F3B": ДКТ: Время на сайте
    "UF_CRM_607968CE63A1F": ДКТ: Страница звонка
    "UF_CRM_607968CE70D3A": ДКТ: Контекст вызова
    "UF_CRM_607968CE7EE62": ДКТ: Custom
    "UF_CRM_607968CE89B09": ДКТ: Имя виджета
    "UF_CRM_607968CE98F5C": ДКТ: Тип заявки
    "UF_CRM_65A8D8C756C8D": ДКТ: client_sid

    "UF_CRM_607968CEAA6BD": riostat

    "UF_CRM_1637552106058":	instagram, Ссылки
    "UF_CRM_1637554689390":	Сайт
    "UF_CRM_1637554795391":	instagram
    "UF_CRM_1637554983001":	Новое поinstagramле
    "UF_CRM_1637556542372":	Сайт
    "UF_CRM_1637560800620":	VK
    "UF_CRM_1654750482": Подписанные договора
    """
