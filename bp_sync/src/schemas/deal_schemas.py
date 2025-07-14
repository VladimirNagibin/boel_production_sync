from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypeVar

from pydantic import Field, field_validator

from models.enums import (
    ProcessingStatusEnum,
    StageSemanticEnum,
    TypePaymentEnum,
    TypeShipmentEnum,
)

from .base_schemas import BaseCreateSchema, BaseUpdateSchema, BitrixValidators

EnumT = TypeVar("EnumT", bound=Enum)


class BaseDeal:
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    # Идентификаторы и основные данные
    additional_info: Optional[str] = Field(None, alias="ADDITIONAL_INFO")

    # Статусы и флаги
    probability: Optional[int] = Field(None, alias="PROBABILITY")
    is_shipment_approved: Optional[bool] = Field(
        None, alias="UF_CRM_60D2AFAEB32CC"
    )
    is_shipment_approved_invoice: Optional[bool] = Field(
        None, alias="UF_CRM_1632738559"
    )

    # Финансовые данные
    payment_grace_period: Optional[int] = Field(
        None, alias="UF_CRM_1656582798"
    )

    # Временные метки
    moved_time: Optional[datetime] = Field(None, alias="MOVED_TIME")
    payment_deadline: Optional[datetime] = Field(
        None, alias="UF_CRM_1632738230"
    )

    # География и источники
    city: Optional[str] = Field(None, alias="UF_CRM_DCT_CITY")
    source_external: Optional[str] = Field(None, alias="UF_CRM_DCT_SOURCE")
    printed_form_id: Optional[str] = Field(None, alias="UF_CRM_1656227383")

    # Связи с другими сущностями
    currency_id: Optional[str] = Field(None, alias="CURRENCY_ID")
    type_id: Optional[str] = Field(None, alias="TYPE_ID")
    lead_id: Optional[int] = Field(None, alias="LEAD_ID")
    company_id: Optional[int] = Field(None, alias="COMPANY_ID")
    contact_id: Optional[int] = Field(None, alias="CONTACT_ID")
    source_id: Optional[str] = Field(None, alias="SOURCE_ID")
    main_activity_id: Optional[int] = Field(None, alias="UF_CRM_1598883361")
    lead_type_id: Optional[str] = Field(None, alias="UF_CRM_612463720554B")
    invoice_stage_id: Optional[str] = Field(None, alias="UF_CRM_1632738354")
    current_stage_id: Optional[str] = Field(None, alias="UF_CRM_1632738604")
    shipping_company_id: Optional[int] = Field(None, alias="UF_CRM_1650617036")
    creation_source_id: Optional[int] = Field(None, alias="UF_CRM_1654577096")
    warehouse_id: Optional[int] = Field(None, alias="UF_CRM_1659326670")
    deal_failure_reason_id: Optional[int] = Field(
        None, alias="UF_CRM_652940014E9A5"
    )

    # Связи по пользователю
    moved_by_id: Optional[int] = Field(None, alias="MOVED_BY_ID")
    defect_expert_id: Optional[int] = Field(None, alias="UF_CRM_1655618547")

    # Поля сервисных сделок
    defect_conclusion: Optional[str] = Field(
        None, alias="UF_CRM_1655618110493"
    )
    defects: list[int] | None = Field(None, alias="UF_CRM_1655615996118")

    # Связанные сделки (доставка)
    parent_deal_id: Optional[int] = Field(None, alias="UF_CRM_1655891443")
    chaild_deal_ids: list[int] | None = Field(None, alias="UF_CRM_1658467259")

    # Маркетинговые метки
    mgo_cc_entry_id: Optional[str] = Field(
        None, alias="UF_CRM_MGO_CC_ENTRY_ID"
    )
    mgo_cc_channel_type: Optional[str] = Field(
        None, alias="UF_CRM_MGO_CC_CHANNEL_TYPE"
    )
    mgo_cc_result: Optional[str] = Field(None, alias="UF_CRM_MGO_CC_RESULT")
    mgo_cc_entry_point: Optional[str] = Field(
        None, alias="UF_CRM_MGO_CC_ENTRY_POINT"
    )
    mgo_cc_create: Optional[datetime] = Field(
        None, alias="UF_CRM_MGO_CC_CREATE"
    )
    mgo_cc_end: Optional[datetime] = Field(None, alias="UF_CRM_MGO_CC_END")
    mgo_cc_tag_id: Optional[str] = Field(None, alias="UF_CRM_MGO_CC_TAG_ID")
    calltouch_site_id: Optional[str] = Field(
        None, alias="UF_CRM_665F0885515AE"
    )
    calltouch_call_id: Optional[str] = Field(
        None, alias="UF_CRM_665F08858FCF0"
    )
    calltouch_request_id: Optional[str] = Field(
        None, alias="UF_CRM_665F0885BB4E2"
    )
    yaclientid: Optional[str] = Field(None, alias="UF_CRM_1739185983784")

    # Социальные профили
    wz_instagram: Optional[str] = Field(None, alias="UF_CRM_63A031829F8E2")
    wz_vc: Optional[str] = Field(None, alias="UF_CRM_63A03182BF864")
    wz_telegram_username: Optional[str] = Field(
        None, alias="UF_CRM_63A03182D063B"
    )
    wz_telegram_id: Optional[str] = Field(None, alias="UF_CRM_63A03182DFB0F")
    wz_avito: Optional[str] = Field(None, alias="UF_CRM_63ABEBD42730D")

    # Валидаторы
    _validate_bool = field_validator(
        "opened",
        "is_shipment_approved",
        "is_shipment_approved_invoice",
        mode="before",
    )(BitrixValidators.convert_to_bool)

    _validate_int = field_validator(
        "external_id",
        "assigned_by_id",
        "created_by_id",
        "modify_by_id",
        "last_activity_by",
        "address_loc_addr_id",
        "probability",
        "payment_grace_period",
        "lead_id",
        "company_id",
        "contact_id",
        "main_activity_id",
        "shipping_company_id",
        "creation_source_id",
        "warehouse_id",
        "deal_failure_reason_id",
        "moved_by_id",
        "defect_expert_id",
        "parent_deal_id",
        mode="before",
        check_fields=False,
    )(BitrixValidators.normalize_int)

    _validate_datetime = field_validator(
        "date_create",
        "date_modify",
        "last_activity_time",
        "moved_time",
        "payment_deadline",
        "mgo_cc_create",
        "mgo_cc_end",
        mode="before",
    )(BitrixValidators.normalize_datetime_fields)

    _validate_list = field_validator(
        "defects",
        "chaild_deal_ids",
        mode="before",
    )(BitrixValidators.normalize_list)


class DealCreate(BaseCreateSchema, BaseDeal):
    """Модель для создания сделок"""

    # Идентификаторы и основные данные
    title: str = Field(..., alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool = Field(False, alias="IS_MANUAL_OPPORTUNITY")
    closed: bool = Field(False, alias="CLOSED")
    is_new: bool = Field(False, alias="IS_NEW")
    is_recurring: bool = Field(False, alias="IS_RECURRING")
    is_return_customer: bool = Field(False, alias="IS_RETURN_CUSTOMER")
    is_repeated_approach: bool = Field(False, alias="IS_REPEATED_APPROACH")

    # Финансовые данные
    opportunity: float = Field(0.0, alias="OPPORTUNITY")

    # Временные метки
    begindate: datetime = Field(..., alias="BEGINDATE")
    closedate: datetime = Field(..., alias="CLOSEDATE")

    # Перечисляемые типы
    stage_semantic_id: StageSemanticEnum = Field(
        StageSemanticEnum.PROSPECTIVE, alias="STAGE_SEMANTIC_ID"
    )
    payment_type: TypePaymentEnum = Field(
        TypePaymentEnum.NOT_DEFINE, alias="UF_CRM_1632738315"
    )
    shipping_type: TypeShipmentEnum = Field(
        TypeShipmentEnum.NOT_DEFINE, alias="UF_CRM_1655141630"
    )
    processing_status: ProcessingStatusEnum = Field(
        ProcessingStatusEnum.NOT_DEFINE, alias="UF_CRM_1750571370"
    )

    # Связи с другими сущностями
    stage_id: str = Field(..., alias="STAGE_ID")
    category_id: int = Field(..., alias="CATEGORY_ID")

    # Валидаторы
    _validate_bool_extra = field_validator(
        "is_manual_opportunity",
        "closed",
        "is_new",
        "is_recurring",
        "is_return_customer",
        "is_repeated_approach",
        mode="before",
    )(BitrixValidators.convert_to_bool)

    # _validate_int_extra = field_validator(
    #    "category_id",
    #    mode="before",
    # )(BitrixValidators.normalize_int)

    _validate_datetime_extra = field_validator(
        "begindate",
        "closedate",
        mode="before",
    )(BitrixValidators.normalize_datetime_fields)

    _validate_float = field_validator("opportunity", mode="before")(
        BitrixValidators.normalize_float
    )

    @field_validator("stage_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_stage_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return BitrixValidators.convert_enum(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )

    @field_validator("payment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_type(cls, v: Any) -> TypePaymentEnum:
        return BitrixValidators.convert_enum(
            v, TypePaymentEnum, TypePaymentEnum.NOT_DEFINE
        )

    @field_validator("shipping_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_shipping_type(cls, v: Any) -> TypeShipmentEnum:
        return BitrixValidators.convert_enum(
            v, TypeShipmentEnum, TypeShipmentEnum.NOT_DEFINE
        )

    @field_validator("processing_status", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_processing_status(cls, v: Any) -> ProcessingStatusEnum:
        return BitrixValidators.convert_enum(
            v, ProcessingStatusEnum, ProcessingStatusEnum.NOT_DEFINE
        )


class DealUpdate(BaseUpdateSchema, BaseDeal):
    """Модель для частичного обновления сделок"""

    # Основные поля с алиасами (все необязательные)
    title: Optional[str] = Field(None, alias="TITLE")

    # Статусы и флаги
    is_manual_opportunity: Optional[bool] = Field(
        None, alias="IS_MANUAL_OPPORTUNITY"
    )
    closed: Optional[bool] = Field(None, alias="CLOSED")
    is_new: Optional[bool] = Field(None, alias="IS_NEW")
    is_recurring: Optional[bool] = Field(None, alias="IS_RECURRING")
    is_return_customer: Optional[bool] = Field(
        None, alias="IS_RETURN_CUSTOMER"
    )
    is_repeated_approach: Optional[bool] = Field(
        None, alias="IS_REPEATED_APPROACH"
    )

    # Финансовые данные
    opportunity: Optional[float] = Field(None, alias="OPPORTUNITY")

    # Временные метки
    begindate: Optional[datetime] = Field(None, alias="BEGINDATE")
    closedate: Optional[datetime] = Field(None, alias="CLOSEDATE")

    # Перечисляемые типы
    stage_semantic_id: StageSemanticEnum | None = Field(
        None, alias="STAGE_SEMANTIC_ID"
    )
    payment_type: TypePaymentEnum | None = Field(
        None, alias="UF_CRM_1632738315"
    )
    shipping_type: TypeShipmentEnum | None = Field(
        None, alias="UF_CRM_1655141630"
    )
    processing_status: ProcessingStatusEnum | None = Field(
        None, alias="UF_CRM_1750571370"
    )

    # Связи с другими сущностями
    stage_id: Optional[str] = Field(None, alias="STAGE_ID")
    category_id: Optional[int] = Field(None, alias="CATEGORY_ID")

    # Валидаторы
    _validate_bool_extra = field_validator(
        "is_manual_opportunity",
        "closed",
        "is_new",
        "is_recurring",
        "is_return_customer",
        "is_repeated_approach",
        mode="before",
    )(BitrixValidators.convert_to_bool)

    _validate_int_extra = field_validator(
        "category_id",
        mode="before",
    )(BitrixValidators.normalize_int)

    _validate_datetime_extra = field_validator(
        "begindate",
        "closedate",
        mode="before",
    )(BitrixValidators.normalize_datetime_fields)

    _validate_float = field_validator("opportunity", mode="before")(
        BitrixValidators.normalize_float
    )

    @field_validator("stage_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_stage_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return BitrixValidators.convert_enum(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )

    @field_validator("payment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_type(cls, v: Any) -> TypePaymentEnum:
        return BitrixValidators.convert_enum(
            v, TypePaymentEnum, TypePaymentEnum.NOT_DEFINE
        )

    @field_validator("shipping_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_shipping_type(cls, v: Any) -> TypeShipmentEnum:
        return BitrixValidators.convert_enum(
            v, TypeShipmentEnum, TypeShipmentEnum.NOT_DEFINE
        )

    @field_validator("processing_status", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_processing_status(cls, v: Any) -> ProcessingStatusEnum:
        return BitrixValidators.convert_enum(
            v, ProcessingStatusEnum, ProcessingStatusEnum.NOT_DEFINE
        )
