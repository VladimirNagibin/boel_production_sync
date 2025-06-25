from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class StageSemanticEnum(str, Enum):
    PROSPECTIVE = "P"
    SUCCESS = "S"
    FAIL = "F"


class TypePaymentEnum(int, Enum):
    PREPAYMENT = 377
    POSTPONEMENT = 379
    PARTPAYMENT = 381
    NOT_DEFINE = 0


class TypeShipmentEnum(int, Enum):
    PICKUP = 515
    DELIVERY_COURIER = 517
    TRANSPORT_COMPANY = 519
    NOT_DEFINE = 0


class ProcessingStatusEnum(int, Enum):
    OK = 781
    AT_RISK = 783
    OVERDUE = 785
    NOT_DEFINE = 0


class DealCreate(BaseModel):  # type: ignore[misc]
    # Основные поля с алиасами для соответствия SQLAlchemy модели
    deal_id: int = Field(..., alias="ID")
    title: str = Field(..., alias="TITLE")
    type_id: str = Field(..., alias="TYPE_ID")
    stage_id: str = Field(..., alias="STAGE_ID")
    probability: Optional[int] = Field(None, alias="PROBABILITY")
    currency_id: str = Field(..., alias="CURRENCY_ID")
    opportunity: float = Field(..., alias="OPPORTUNITY")
    is_manual_opportunity: bool = Field(..., alias="IS_MANUAL_OPPORTUNITY")
    lead_id: int = Field(..., alias="LEAD_ID")
    company_id: int = Field(..., alias="COMPANY_ID")
    contact_id: Optional[int] = Field(None, alias="CONTACT_ID")
    begindate: datetime = Field(..., alias="BEGINDATE")
    closedate: datetime = Field(..., alias="CLOSEDATE")
    assigned_by_id: int = Field(..., alias="ASSIGNED_BY_ID")
    created_by_id: int = Field(..., alias="CREATED_BY_ID")
    modify_by_id: int = Field(..., alias="MODIFY_BY_ID")
    date_create: datetime = Field(..., alias="DATE_CREATE")
    date_modify: datetime = Field(..., alias="DATE_MODIFY")
    opened: bool = Field(..., alias="OPENED")
    closed: bool = Field(..., alias="CLOSED")
    comments: Optional[str] = Field(None, alias="COMMENTS")
    additional_info: Optional[str] = Field(None, alias="ADDITIONAL_INFO")
    category_id: int = Field(..., alias="CATEGORY_ID")
    stage_semantic_id: StageSemanticEnum = Field(
        ..., alias="STAGE_SEMANTIC_ID"
    )
    is_new: bool = Field(..., alias="IS_NEW")
    is_recurring: bool = Field(..., alias="IS_RECURRING")
    is_return_customer: bool = Field(..., alias="IS_RETURN_CUSTOMER")
    is_repeated_approach: bool = Field(..., alias="IS_REPEATED_APPROACH")
    source_id: str = Field(..., alias="SOURCE_ID")
    source_description: Optional[str] = Field(None, alias="SOURCE_DESCRIPTION")
    originator_id: Optional[str] = Field(None, alias="ORIGINATOR_ID")
    origin_id: Optional[str] = Field(None, alias="ORIGIN_ID")
    moved_by_id: int = Field(..., alias="MOVED_BY_ID")
    moved_time: datetime = Field(..., alias="MOVED_TIME")
    last_activity_time: datetime = Field(..., alias="LAST_ACTIVITY_TIME")
    last_communication_time: Optional[datetime] = Field(
        None, alias="LAST_COMMUNICATION_TIME"
    )
    last_activity_by: int = Field(..., alias="LAST_ACTIVITY_BY")

    # Пользовательские поля
    main_activity_id: Optional[int] = Field(None, alias="UF_CRM_1598883361")
    city: Optional[str] = Field(None, alias="UF_CRM_DCT_CITY")
    is_shipment_approved: Optional[bool] = Field(
        None, alias="UF_CRM_60D2AFAEB32CC"
    )
    lead_type_id: Optional[str] = Field(None, alias="UF_CRM_612463720554B")
    payment_deadline: Optional[datetime] = Field(
        None, alias="UF_CRM_1632738230"
    )
    payment_type: TypePaymentEnum = Field(
        TypePaymentEnum.NOT_DEFINE, alias="UF_CRM_1632738315"
    )
    invoice_stage_id: str = Field(..., alias="UF_CRM_1632738354")
    is_shipment_approved_invoice: Optional[bool] = Field(
        None, alias="UF_CRM_1632738559"
    )
    current_stage_id: str = Field(..., alias="UF_CRM_1632738604")
    shipping_company_id: int = Field(..., alias="UF_CRM_1650617036")
    creation_source_id: int = Field(..., alias="UF_CRM_1654577096")
    shipping_type: TypeShipmentEnum = Field(
        TypeShipmentEnum.NOT_DEFINE, alias="UF_CRM_1655141630"
    )
    parent_deal_id: Optional[int] = Field(None, alias="UF_CRM_1655891443")
    id_printed_form: Optional[str] = Field(None, alias="UF_CRM_1656227383")
    payment_grace_period: Optional[int] = Field(
        None, alias="UF_CRM_1656582798"
    )
    warehouse_id: int = Field(..., alias="UF_CRM_1659326670")
    processing_status: ProcessingStatusEnum = Field(
        ProcessingStatusEnum.NOT_DEFINE, alias="UF_CRM_1750571370"
    )

    # Валидаторы
    @validator(
        "opened",
        "closed",
        "is_new",
        "is_recurring",
        "is_return_customer",
        "is_repeated_approach",
        "is_manual_opportunity",
        "is_shipment_approved",
        "is_shipment_approved_invoice",
        pre=True,
    )
    def convert_yn_to_bool(cls, v):  # type: ignore[no-untyped-def]
        if isinstance(v, str):
            return v == "Y" or v == "1"
        return v

    @validator(
        "contact_id",
        "comments",
        "additional_info",
        "source_description",
        "originator_id",
        "origin_id",
        "lead_type_id",
        "parent_deal_id",
        "id_printed_form",
        "payment_grace_period",
        pre=True,
    )
    def empty_string_to_none(cls, v):  # type: ignore[no-untyped-def]
        if v == "":
            return None
        return v

    @validator("payment_type", "shipping_type", "processing_status", pre=True)
    def convert_to_enum(cls, v):  # type: ignore[no-untyped-def]
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        extra = "forbid"  # Запрещает дополнительные поля ???

    @validator("PROBABILITY")  # type: ignore[misc]
    def validate_probability(cls, v: Optional[int]) -> Optional[int]:
        """Кастомная валидация вероятности сделки"""
        if v is not None and (0 <= v <= 100):
            raise ValueError("Probability must be between 0 and 100")
        return v


class DealResponse(BaseModel):  # type: ignore[misc]
    """Схема для ответа API"""

    id: int = Field(..., description="Внутренний ID в базе данных")
    deal_id: int = Field(..., description="Уникальный ID сделки")
    title: str = Field(..., description="Название сделки")
    type_id: str = Field(..., description="ID типа сделки")
    stage_id: str = Field(..., description="ID стадии сделки")
    currency_id: str = Field(..., description="ID валюты")
    opportunity: float = Field(..., description="Сумма сделки")
    is_manual_opportunity: bool = Field(
        ..., description="Ручное изменение суммы"
    )
    probability: Optional[int] = Field(
        None, description="Вероятность закрытия"
    )

    class Config:
        orm_mode = True  # Для автоматической конвертации ORM-объектов


class DealListResponse(BaseModel):  # type: ignore[misc]
    """Схема для ответа со списком сделок"""

    items: list[DealResponse]
    count: int
