from datetime import datetime

from pydantic import Field, field_validator

from .base_schemas import (
    AddressMixin,
    BaseCreateSchema,
    BaseUpdateSchema,
    CommunicationChannel,
    HasCommunicationCreateMixin,
    HasCommunicationUpdateMixin,
)


class BaseCompany:
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    # Финансы
    banking_details: str | None = Field(None, alias="BANKING_DETAILS")

    # Адреса
    address_legal: str | None = Field(None, alias="ADDRESS_LEGAL")
    address_company: str | None = Field(None, alias="UF_CRM_1596031539")
    province_company: str | None = Field(None, alias="UF_CRM_1596031556")

    # Статусы и флаги
    is_shipment_approved: bool | None = Field(
        None, alias="UF_CRM_61974C16DBFBF"
    )

    # Временные метки
    date_last_shipment: datetime | None = Field(
        None, alias="UF_CRM_1623835088"
    )

    # География и источники
    city: str | None = Field(None, alias="UF_CRM_607968CE029D8")
    source_external: str | None = Field(None, alias="UF_CRM_607968CE0F3A4")
    origin_version: str | None = Field(None, alias="ORIGIN_VERSION")

    # Связи с другими сущностями
    contracts: list[str] | None = Field(None, alias="UF_CRM_1623833623")
    currency_id: str | None = Field(None, alias="CURRENCY_ID")
    company_type_id: str | None = Field(None, alias="COMPANY_TYPE")
    contact_id: int | None = Field(None, alias="CONTACT_ID")
    lead_id: int | None = Field(None, alias="LEAD_ID")
    source_id: str | None = Field(None, alias="UF_CRM_1637554945")
    main_activity_id: int | None = Field(None, alias="UF_CRM_1598882910")
    deal_failure_reason_id: int | None = Field(
        None, alias="UF_CRM_65A8D8C72059A"
    )
    deal_type_id: str | None = Field(None, alias="UF_CRM_61974C16F0F71")
    shipping_company_id: int | None = Field(
        None, alias="UF_CRM_1631941968"
    )  # "UF_CRM_1631903199"ссылка на объект компании отгрузки.
    # Дубль со ссылкой на ИД компании отгрузки.
    industry_id: str | None = Field(None, alias="INDUSTRY")
    employees_id: str | None = Field(None, alias="EMPLOYEES")
    parent_company_id: int | None = Field(None, alias="UF_CRM_1623833602")

    # Маркетинговые метки
    mgo_cc_entry_id: str | None = Field(None, alias="UF_CRM_63F2F6E58EE14")
    mgo_cc_channel_type: str | None = Field(None, alias="UF_CRM_63F2F6E5A6DE8")
    mgo_cc_result: str | None = Field(None, alias="UF_CRM_63F2F6E5BEAEE")
    mgo_cc_entry_point: str | None = Field(None, alias="UF_CRM_63F2F6E5D8B28")
    mgo_cc_create: datetime | None = Field(None, alias="UF_CRM_63F2F6E5F1691")
    mgo_cc_end: datetime | None = Field(None, alias="UF_CRM_63F2F6E6181EE")
    mgo_cc_tag_id: str | None = Field(None, alias="UF_CRM_63F2F6E630D9C")
    calltouch_site_id: str | None = Field(None, alias="UF_CRM_66618114BF72A")
    calltouch_call_id: str | None = Field(None, alias="UF_CRM_66618115024C3")
    calltouch_request_id: str | None = Field(
        None, alias="UF_CRM_66618115280F4"
    )

    # Социальные профили
    wz_instagram: str | None = Field(None, alias="UF_CRM_63F2F6E50BBDC")
    wz_vc: str | None = Field(None, alias="UF_CRM_63F2F6E52BC88")
    wz_telegram_username: str | None = Field(
        None, alias="UF_CRM_63F2F6E544CDC"
    )
    wz_telegram_id: str | None = Field(None, alias="UF_CRM_63F2F6E5602C1")
    wz_avito: str | None = Field(None, alias="UF_CRM_63F2F6E5766C6")

    # Коммуникации
    phone: list[CommunicationChannel] | None = Field(None, alias="PHONE")
    email: list[CommunicationChannel] | None = Field(None, alias="EMAIL")
    web: list[CommunicationChannel] | None = Field(None, alias="WEB")
    im: list[CommunicationChannel] | None = Field(None, alias="IM")
    link: list[CommunicationChannel] | None = Field(None, alias="LINK")

    # Для договора
    position_head: str | None = Field(None, alias="UF_CRM_1630507939")
    basis_operates: str | None = Field(None, alias="UF_CRM_1630508048")
    position_head_genitive: str | None = Field(None, alias="UF_CRM_1632315102")
    basis_operates_genitive: str | None = Field(
        None, alias="UF_CRM_1632315157"
    )
    payment_delay_genitive: str | None = Field(None, alias="UF_CRM_1632315337")
    full_name_genitive: str | None = Field(None, alias="UF_CRM_1633583719")
    current_contract: str | None = Field(None, alias="UF_CRM_1623915176")
    current_number_contract: str | None = Field(
        None, alias="UF_CRM_1654683828"
    )

    # Дополнительные ответственные
    additional_responsible: list[int] | None = Field(
        None, alias="UF_CRM_1629106458"
    )

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]


class CompanyCreate(
    BaseCreateSchema, BaseCompany, AddressMixin, HasCommunicationCreateMixin
):
    """Модель для создания контактов"""

    # Идентификаторы и основные данные
    title: str = Field(..., alias="TITLE")

    # Финансы
    revenue: float = Field(0.0, alias="REVENUE")

    # Статусы и флаги
    is_my_company: bool = Field(False, alias="IS_MY_COMPANY")


class CompanyUpdate(
    BaseUpdateSchema, BaseCompany, AddressMixin, HasCommunicationUpdateMixin
):
    """Модель для частичного обновления контактов"""

    # Идентификаторы и основные данные
    title: str | None = Field(None, alias="TITLE")

    # Финансы
    revenue: float | None = Field(None, alias="REVENUE")

    # Статусы и флаги
    is_my_company: bool | None = Field(None, alias="IS_MY_COMPANY")
