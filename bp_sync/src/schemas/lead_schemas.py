from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from models.enums import StageSemanticEnum

from .base_schemas import (
    AddressMixin,
    BaseCreateSchema,
    BaseUpdateSchema,
    BitrixValidators,
    CommunicationChannel,
    HasCommunicationCreateMixin,
    HasCommunicationUpdateMixin,
)


class BaseLead:
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    # Идентификаторы и основные данные
    name: str | None = Field(None, alias="NAME")
    second_name: str | None = Field(None, alias="SECOND_NAME")
    last_name: str | None = Field(None, alias="LAST_NAME")
    post: str | None = Field(None, alias="POST")
    company_title: str | None = Field(None, alias="COMPANY_TITLE")

    # Статусы и флаги
    is_shipment_approved: bool | None = Field(None, alias="UF_CRM_1623830089")

    # Временные метки
    birthdate: datetime | None = Field(None, alias="BIRTHDATE")
    date_closed: datetime | None = Field(..., alias="DATE_CLOSED")
    moved_time: datetime | None = Field(None, alias="MOVED_TIME")

    # География и источники
    city: str | None = Field(None, alias="UF_CRM_DCT_CITY")
    status_description: str | None = Field(None, alias="STATUS_DESCRIPTION")
    source_external: str | None = Field(None, alias="UF_CRM_DCT_SOURCE")

    # Связи с другими сущностями
    currency_id: str | None = Field(None, alias="CURRENCY_ID")
    type_id: str | None = Field(None, alias="UF_CRM_1629271075")
    company_id: int | None = Field(None, alias="COMPANY_ID")
    contact_id: int | None = Field(None, alias="CONTACT_ID")
    source_id: str | None = Field(None, alias="SOURCE_ID")
    main_activity_id: int | None = Field(None, alias="UF_CRM_1598882174")
    deal_failure_reason_id: int | None = Field(None, alias="UF_CRM_1697036607")

    # Связи по пользователю
    moved_by_id: int | None = Field(None, alias="MOVED_BY_ID")

    # Маркетинговые метки
    mgo_cc_entry_id: str | None = Field(None, alias="UF_CRM_MGO_CC_ENTRY_ID")
    mgo_cc_channel_type: str | None = Field(
        None, alias="UF_CRM_MGO_CC_CHANNEL_TYPE"
    )
    mgo_cc_result: str | None = Field(None, alias="UF_CRM_MGO_CC_RESULT")
    mgo_cc_entry_point: str | None = Field(
        None, alias="UF_CRM_MGO_CC_ENTRY_POINT"
    )
    mgo_cc_create: datetime | None = Field(None, alias="UF_CRM_MGO_CC_CREATE")
    mgo_cc_end: datetime | None = Field(None, alias="UF_CRM_MGO_CC_END")
    mgo_cc_tag_id: str | None = Field(None, alias="UF_CRM_MGO_CC_TAG_ID")
    calltouch_site_id: str | None = Field(None, alias="UF_CRM_CALLTOUCHT413")
    calltouch_call_id: str | None = Field(None, alias="UF_CRM_CALLTOUCH3ZFT")
    calltouch_request_id: str | None = Field(
        None, alias="UF_CRM_CALLTOUCHWG9P"
    )
    yaclientid: str | None = Field(None, alias="UF_CRM_1739432591418")

    # Социальные профили
    wz_instagram: str | None = Field(None, alias="UF_CRM_INSTAGRAM_WZ")
    wz_vc: str | None = Field(None, alias="UF_CRM_VK_WZ")
    wz_telegram_username: str | None = Field(
        None, alias="UF_CRM_TELEGRAMUSERNAME_WZ"
    )
    wz_telegram_id: str | None = Field(None, alias="UF_CRM_TELEGRAMID_WZ")
    wz_avito: str | None = Field(None, alias="UF_CRM_AVITO_WZ")

    # Коммуникации
    phone: list[CommunicationChannel] | None = Field(None, alias="PHONE")
    email: list[CommunicationChannel] | None = Field(None, alias="EMAIL")
    web: list[CommunicationChannel] | None = Field(None, alias="WEB")
    im: list[CommunicationChannel] | None = Field(None, alias="IM")
    link: list[CommunicationChannel] | None = Field(None, alias="LINK")

    # Основные поля с алиасами (все необязательные)
    title: str | None = Field(None, alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool | None = Field(
        None, alias="IS_MANUAL_OPPORTUNITY"
    )
    is_return_customer: bool | None = Field(None, alias="IS_RETURN_CUSTOMER")

    # Финансовые данные
    opportunity: float | None = Field(None, alias="OPPORTUNITY")

    # Перечисляемые типы
    status_semantic_id: StageSemanticEnum | None = Field(
        None, alias="STATUS_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    status_id: str | None = Field(None, alias="STATUS_ID")

    # Валидаторы
    _validate_bool = field_validator(
        "has_phone",
        "has_email",
        "has_imol",
        "opened",
        "is_shipment_approved",
        "is_return_customer",
        "is_manual_opportunity",
        mode="before",
    )(BitrixValidators.convert_to_bool)

    _validate_int = field_validator(
        "external_id",
        "assigned_by_id",
        "created_by_id",
        "modify_by_id",
        "last_activity_by",
        "address_loc_addr_id",
        "company_id",
        "contact_id",
        "main_activity_id",
        "deal_failure_reason_id",
        "moved_by_id",
        mode="before",
    )(BitrixValidators.normalize_int)

    _validate_datetime = field_validator(
        "date_create",
        "date_modify",
        "last_activity_time",
        "birthdate",
        "date_closed",
        "moved_time",
        "mgo_cc_create",
        "mgo_cc_end",
        mode="before",
    )(BitrixValidators.normalize_datetime_fields)

    _validate_list = field_validator(
        "phone",
        "email",
        "web",
        "im",
        "link",
        mode="before",
    )(BitrixValidators.normalize_list)

    _validate_float = field_validator("opportunity", mode="before")(
        BitrixValidators.normalize_float
    )

    @field_validator("status_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_status_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return BitrixValidators.convert_enum(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )


class LeadCreate(
    BaseCreateSchema, BaseLead, AddressMixin, HasCommunicationCreateMixin
):
    """Модель для создания лидов"""

    # Идентификаторы и основные данные
    title: str = Field(..., alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool = Field(False, alias="IS_MANUAL_OPPORTUNITY")
    is_return_customer: bool = Field(False, alias="IS_RETURN_CUSTOMER")

    # Финансовые данные
    opportunity: float = Field(0.0, alias="OPPORTUNITY")

    # Перечисляемые типы
    status_semantic_id: StageSemanticEnum = Field(
        StageSemanticEnum.PROSPECTIVE, alias="STATUS_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    status_id: str = Field(..., alias="STATUS_ID")


class LeadUpdate(
    BaseUpdateSchema, BaseLead, AddressMixin, HasCommunicationUpdateMixin
):
    """Модель для частичного обновления лидов"""

    ...
