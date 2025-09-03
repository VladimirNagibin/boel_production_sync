from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import Field, field_validator

from models.enums import (
    DualTypePaymentEnum,
    DualTypeShipmentEnum,
    MethodPaymentEnum,
)

from .base_schemas import BitrixValidators, CoreCreateSchema, CoreUpdateSchema
from .fields import FIELDS_INVOICE


class BaseInvoice:
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_INVOICE

    # Идентификаторы и основные данные
    account_number: str | None = Field(None, alias="accountNumber")
    xml_id: str | None = Field(None, alias="xmlId")
    proposal_id: int | None = Field(None, alias="parentId7")
    category_id: int | None = Field(None, alias="categoryId")
    comments: Optional[str] = Field(None, alias="comments")

    # Статусы и флаги
    is_shipment_approved: bool | None = Field(
        None, alias="ufCrm_62B53CC589745"
    )
    check_repeat: bool | None = Field(
        None, alias="ufCrm_SMART_INVOICE_1651138836085"
    )
    is_loaded: bool | None = Field(
        None, alias="webformId"
    )  # Выгружено в 1с (Создано CRM-формой) 1 - True

    # Финансовые данные
    payment_grace_period: int | None = Field(
        None, alias="ufCrm_SMART_INVOICE_1656584515597"
    )

    # Временные метки
    begindate: Optional[datetime] = Field(None, alias="begindate")
    closedate: Optional[datetime] = Field(None, alias="closedate")
    moved_time: Optional[datetime] = Field(None, alias="movedTime")
    last_call_time: Optional[datetime] = Field(
        None, alias="lastCommunicationCallTime"
    )
    last_email_time: Optional[datetime] = Field(
        None, alias="lastCommunicationEmailTime"
    )
    last_imol_time: Optional[datetime] = Field(
        None, alias="lastCommunicationImolTime"
    )
    last_webform_time: Optional[datetime] = Field(
        None, alias="lastCommunicationWebformTime"
    )

    # География и источники
    city: Optional[str] = Field(None, alias="ufCrm_6260D1A89E13A")
    source_external: Optional[str] = Field(None, alias="ufCrm_6260D1A8A8490")
    source_description: Optional[str] = Field(None, alias="sourceDescription")
    printed_form_id: str | None = Field(
        None, alias="ufCrm_SMART_INVOICE_1651138396589"
    )

    # Связи с другими сущностями
    currency_id: Optional[str] = Field(None, alias="currencyId")
    company_id: Optional[int] = Field(None, alias="companyId")
    contact_id: Optional[int] = Field(None, alias="contactId")
    deal_id: Optional[int] = Field(None, alias="parentId2")
    invoice_stage_id: Optional[str] = Field(None, alias="stageId")
    previous_stage_id: Optional[str] = Field(None, alias="previousStageId")
    current_stage_id: Optional[str] = Field(
        None, alias="ufCrm_SMART_INVOICE_1651509493"
    )
    source_id: Optional[str] = Field(None, alias="sourceId")
    main_activity_id: Optional[int] = Field(None, alias="ufCrm_6260D1A85BBB9")
    warehouse_id: Optional[int] = Field(
        None, alias="ufCrm_SMART_INVOICE_1651083239729"
    )
    creation_source_id: Optional[int] = Field(
        None, alias="ufCrm_62B53CC5943F6"
    )
    invoice_failure_reason_id: Optional[int] = Field(
        None, alias="ufCrm_6721D5B0EE615"
    )
    shipping_company_id: Optional[int] = Field(None, alias="mycompanyId")
    type_id: Optional[str] = Field(None, alias="ufCrm_6260D1A936963")

    # Связи по пользователю
    moved_by_id: Optional[int] = Field(None, alias="movedBy")

    # Маркетинговые метки
    mgo_cc_entry_id: Optional[str] = Field(None, alias="ufCrm_6721D5AF2F6F9")
    mgo_cc_channel_type: Optional[str] = Field(
        None, alias="ufCrm_6721D5AF6A70F"
    )
    mgo_cc_result: Optional[str] = Field(None, alias="ufCrm_6721D5AFA85B4")
    mgo_cc_entry_point: Optional[str] = Field(
        None, alias="ufCrm_6721D5AFE18DE"
    )
    mgo_cc_create: Optional[datetime] = Field(
        None, alias="ufCrm_6721D5B03E0CE"
    )
    mgo_cc_end: Optional[datetime] = Field(None, alias="ufCrm_6721D5B0797AD")
    mgo_cc_tag_id: Optional[str] = Field(None, alias="ufCrm_6721D5B0B69F5")
    calltouch_site_id: Optional[str] = Field(None, alias="ufCrm_6721D5B1853FA")
    calltouch_call_id: Optional[str] = Field(None, alias="ufCrm_6721D5B1C3D16")
    calltouch_request_id: Optional[str] = Field(
        None, alias="ufCrm_6721D5B208140"
    )
    yaclientid: Optional[str] = Field(None, alias="ufCrm_67AC443A81F1C")

    # Социальные профили
    wz_instagram: Optional[str] = Field(None, alias="ufCrm_6721D5ADF30BB")
    wz_vc: Optional[str] = Field(None, alias="ufCrm_6721D5AE366D1")
    wz_telegram_username: Optional[str] = Field(
        None, alias="ufCrm_6721D5AE6BE98"
    )
    wz_telegram_id: Optional[str] = Field(None, alias="ufCrm_6721D5AEA56E0")
    wz_avito: Optional[str] = Field(None, alias="ufCrm_6721D5AEDFA5C")

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]

    @field_validator(
        "last_communication_time", mode="before"
    )  # type: ignore[misc]
    @classmethod
    def convert_datetime_with_tz_to_(cls, value: Any) -> datetime:
        """Автоматическое преобразование даты с таймзоной в без"""
        if isinstance(value, datetime) and value.tzinfo:
            return value.replace(tzinfo=None)
        return value  # type: ignore[no-any-return]


class InvoiceCreate(BaseInvoice, CoreCreateSchema):
    """Модель для создания счетов"""

    # Идентификаторы и основные данные
    title: str = Field(..., alias="title")

    # Финансовые данные
    opportunity: float = Field(0.0, alias="opportunity")

    # Статусы и флаги
    is_manual_opportunity: bool = Field(False, alias="isManualOpportunity")
    opened: bool = Field(True, alias="opened")

    # Перечисляемые типы
    payment_method: MethodPaymentEnum = Field(
        MethodPaymentEnum.NOT_DEFINE, alias="ufCrm_SMART_INVOICE_1651083629638"
    )
    payment_type: DualTypePaymentEnum = Field(
        DualTypePaymentEnum.NOT_DEFINE,
        alias="ufCrm_SMART_INVOICE_1651114959541",
    )
    shipment_type: DualTypeShipmentEnum = Field(
        DualTypeShipmentEnum.NOT_DEFINE, alias="ufCrm_62B53CC5A2EDF"
    )

    @field_validator("payment_method", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_method(cls, v: Any) -> MethodPaymentEnum:
        return BitrixValidators.convert_enum(
            v, MethodPaymentEnum, MethodPaymentEnum.NOT_DEFINE
        )

    @field_validator("payment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_type(cls, v: Any) -> DualTypePaymentEnum:
        return BitrixValidators.convert_enum(
            v, DualTypePaymentEnum, DualTypePaymentEnum.NOT_DEFINE
        )

    @field_validator("shipment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_shipment_type(cls, v: Any) -> DualTypeShipmentEnum:
        return BitrixValidators.convert_enum(
            v, DualTypeShipmentEnum, DualTypeShipmentEnum.NOT_DEFINE
        )


class InvoiceUpdate(BaseInvoice, CoreUpdateSchema):
    """Модель для частичного обновления счетов"""

    # Идентификаторы и основные данные
    title: str | None = Field(default=None, alias="title")

    # Финансовые данные
    opportunity: float | None = Field(default=None, alias="opportunity")

    # Статусы и флаги
    is_manual_opportunity: bool | None = Field(
        default=None, alias="isManualOpportunity"
    )
    opened: bool | None = Field(default=None, alias="opened")

    # Перечисляемые типы
    payment_method: MethodPaymentEnum | None = Field(
        default=None, alias="ufCrm_SMART_INVOICE_1651083629638"
    )
    payment_type: DualTypePaymentEnum | None = Field(
        default=None,
        alias="ufCrm_SMART_INVOICE_1651114959541",
    )
    shipment_type: DualTypeShipmentEnum | None = Field(
        default=None, alias="ufCrm_62B53CC5A2EDF"
    )

    @field_validator("payment_method", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_method(cls, v: Any) -> MethodPaymentEnum:
        return BitrixValidators.convert_enum(
            v, MethodPaymentEnum, MethodPaymentEnum.NOT_DEFINE
        )

    @field_validator("payment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_type(cls, v: Any) -> DualTypePaymentEnum:
        return BitrixValidators.convert_enum(
            v, DualTypePaymentEnum, DualTypePaymentEnum.NOT_DEFINE
        )

    @field_validator("shipment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_shipment_type(cls, v: Any) -> DualTypeShipmentEnum:
        return BitrixValidators.convert_enum(
            v, DualTypeShipmentEnum, DualTypeShipmentEnum.NOT_DEFINE
        )
