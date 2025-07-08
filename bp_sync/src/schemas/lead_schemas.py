from datetime import datetime
from enum import Enum
from typing import Any, Optional, Type, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from models.enums import StageSemanticEnum

from .base_schemas import BaseCreateSchema, BaseUpdateSchema

EnumT = TypeVar("EnumT", bound=Enum)


class CommunicationChannel(BaseModel):  # type: ignore[misc]
    """Схема коммуникации"""

    external_id: int | None = Field(None, alias="ID")
    type_id: str | None = Field(None, alias="TYPE_ID")
    value_type: str = Field(..., alias="VALUE_TYPE")
    value: str = Field(..., alias="VALUE")

    #  model_config = ConfigDict(from_attributes=True)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class LeadCreate(BaseCreateSchema):
    # Поля с алиасами для соответствия SQLAlchemy модели

    # Идентификаторы и основные данные
    # external_id: int = Field(..., alias="ID")
    title: str = Field(..., alias="TITLE")
    comments: Optional[str] = Field(None, alias="COMMENTS")
    name: Optional[str] = Field(None, alias="NAME")
    second_name: Optional[str] = Field(None, alias="SECOND_NAME")
    last_name: Optional[str] = Field(None, alias="LAST_NAME")
    post: Optional[str] = Field(None, alias="POST")
    company_title: Optional[str] = Field(None, alias="COMPANY_TITLE")

    # Статусы и флаги
    is_manual_opportunity: bool = Field(False, alias="IS_MANUAL_OPPORTUNITY")
    opened: bool = Field(True, alias="OPENED")
    is_return_customer: bool = Field(False, alias="IS_RETURN_CUSTOMER")
    is_shipment_approved: Optional[bool] = Field(
        None, alias="UF_CRM_1623830089"
    )
    has_phone: bool = Field(..., alias="HAS_PHONE")
    has_email: bool = Field(..., alias="HAS_EMAIL")
    has_imol: bool = Field(..., alias="HAS_IMOL")

    # Финансовые данные
    opportunity: float = Field(0.0, alias="OPPORTUNITY")

    # Временные метки
    birthdate: Optional[datetime] = Field(None, alias="BIRTHDATE")
    date_closed: datetime = Field(..., alias="DATE_CLOSED")
    date_create: datetime = Field(..., alias="DATE_CREATE")
    date_modify: datetime = Field(..., alias="DATE_MODIFY")
    moved_time: Optional[datetime] = Field(None, alias="MOVED_TIME")
    last_activity_time: Optional[datetime] = Field(
        None, alias="LAST_ACTIVITY_TIME"
    )
    last_communication_time: Optional[datetime] = Field(
        None, alias="LAST_COMMUNICATION_TIME"
    )

    # География и источники
    city: Optional[str] = Field(None, alias="UF_CRM_DCT_CITY")
    source_description: Optional[str] = Field(None, alias="SOURCE_DESCRIPTION")
    status_description: Optional[str] = Field(None, alias="STATUS_DESCRIPTION")
    source_external: Optional[str] = Field(None, alias="UF_CRM_DCT_SOURCE")
    originator_id: Optional[str] = Field(None, alias="ORIGINATOR_ID")
    origin_id: Optional[str] = Field(None, alias="ORIGIN_ID")

    # Адрес
    address: Optional[str] = Field(None, alias="ADDRESS")
    address_2: Optional[str] = Field(None, alias="ADDRESS_2")
    address_city: Optional[str] = Field(None, alias="ADDRESS_CITY")
    address_postal_code: Optional[str] = Field(
        None, alias="ADDRESS_POSTAL_CODE"
    )
    address_region: Optional[str] = Field(None, alias="ADDRESS_REGION")
    address_province: Optional[str] = Field(None, alias="ADDRESS_PROVINCE")
    address_country: Optional[str] = Field(None, alias="ADDRESS_COUNTRY")
    address_country_code: Optional[str] = Field(
        None, alias="ADDRESS_COUNTRY_CODE"
    )
    address_loc_addr_id: Optional[int] = Field(
        None, alias="ADDRESS_LOC_ADDR_ID"
    )

    # Перечисляемые типы
    status_semantic_id: StageSemanticEnum = Field(
        StageSemanticEnum.PROSPECTIVE, alias="STATUS_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    currency_id: Optional[str] = Field(None, alias="CURRENCY_ID")
    type_id: Optional[str] = Field(None, alias="UF_CRM_1629271075")
    status_id: str = Field(..., alias="STATUS_ID")
    company_id: Optional[int] = Field(None, alias="COMPANY_ID")
    contact_id: Optional[int] = Field(None, alias="CONTACT_ID")
    source_id: Optional[str] = Field(None, alias="SOURCE_ID")
    main_activity_id: Optional[int] = Field(None, alias="UF_CRM_1598882174")
    deal_failure_reason_id: Optional[int] = Field(
        None, alias="UF_CRM_1697036607"
    )

    # Связи по пользователю
    assigned_by_id: int = Field(..., alias="ASSIGNED_BY_ID")
    created_by_id: int = Field(..., alias="CREATED_BY_ID")
    modify_by_id: int = Field(..., alias="MODIFY_BY_ID")
    moved_by_id: Optional[int] = Field(None, alias="MOVED_BY_ID")
    last_activity_by: Optional[int] = Field(None, alias="LAST_ACTIVITY_BY")

    # Маркетинговые метки
    utm_source: Optional[str] = Field(None, alias="UTM_SOURCE")
    utm_medium: Optional[str] = Field(None, alias="UTM_MEDIUM")
    utm_campaign: Optional[str] = Field(None, alias="UTM_CAMPAIGN")
    utm_content: Optional[str] = Field(None, alias="UTM_CONTENT")
    utm_term: Optional[str] = Field(None, alias="UTM_TERM")
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
        None, alias="UF_CRM_CALLTOUCHT413"
    )
    calltouch_call_id: Optional[str] = Field(
        None, alias="UF_CRM_CALLTOUCH3ZFT"
    )
    calltouch_request_id: Optional[str] = Field(
        None, alias="UF_CRM_CALLTOUCHWG9P"
    )
    yaclientid: Optional[str] = Field(None, alias="UF_CRM_1739432591418")

    # Социальные профили
    wz_instagram: Optional[str] = Field(None, alias="UF_CRM_INSTAGRAM_WZ")
    wz_vc: Optional[str] = Field(None, alias="UF_CRM_VK_WZ")
    wz_telegram_username: Optional[str] = Field(
        None, alias="UF_CRM_TELEGRAMUSERNAME_WZ"
    )
    wz_telegram_id: Optional[str] = Field(None, alias="UF_CRM_TELEGRAMID_WZ")
    wz_avito: Optional[str] = Field(None, alias="UF_CRM_AVITO_WZ")

    # Коммуникации
    phone: Optional[list[CommunicationChannel] | None] = Field(
        None, alias="PHONE"
    )
    email: Optional[list[CommunicationChannel] | None] = Field(
        None, alias="EMAIL"
    )
    web: Optional[list[CommunicationChannel] | None] = Field(None, alias="WEB")
    im: Optional[list[CommunicationChannel] | None] = Field(None, alias="IM")
    link: Optional[list[CommunicationChannel] | None] = Field(
        None, alias="LINK"
    )

    # Универсальный валидатор для всех полей
    @model_validator(mode="before")  # type: ignore[misc]
    @classmethod
    def normalize_empty_values(cls, data: Any) -> Any:
        """Преобразует пустые строки в None для всех полей"""
        if not isinstance(data, dict):
            return data

        for field in list(data.keys()):
            value = data[field]
            if isinstance(value, str) and value.strip() == "":
                data[field] = None
        return data

    # Валидаторы для преобразования значений
    @field_validator(
        "opened",
        "is_return_customer",
        "is_manual_opportunity",
        "is_shipment_approved",
        "has_phone",
        "has_email",
        "has_imol",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def convert_to_bool(cls, v: Any) -> bool:
        """Преобразует различные форматы в булевы значения"""
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.upper() in ("Y", "1", "TRUE", "T", "YES")
        if isinstance(v, int):
            return bool(v)
        return False

    @field_validator(
        "contact_id",
        "main_activity_id",
        "deal_failure_reason_id",
        "assigned_by_id",
        "created_by_id",
        "modify_by_id",
        "moved_by_id",
        "last_activity_by",
        "address_loc_addr_id",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_numeric_fields(cls, v: Any) -> Optional[int]:
        """Обрабатывает числовые поля: пустые значения → None, строки → int"""
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator(
        "opportunity",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_float_fields(cls, v: Any) -> Optional[float]:
        """
        Обрабатывает числовые поля: пустые значения → None, строки → float
        """
        if v is None or v == "":
            return None
        try:
            # v = ''.join(v.split())
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator(
        "company_id",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_company_id_fields(cls, v: Any) -> Optional[int]:
        """Обрабатывает числовые поля: 0 → None, строки → int"""
        if v is None or v == "" or v == "0":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _convert_enum_value(
        cls, v: Any, enum_type: Type[EnumT], default: EnumT
    ) -> EnumT:
        """Вспомогательная функция для преобразования значений enum"""
        if v is None or v == "":
            return default

        try:
            # Пробуем преобразовать строку в число
            if isinstance(v, str) and v.isdigit():
                v = int(v)

            # Пробуем найти значение в enum
            return enum_type(v)
        except (ValueError, TypeError):
            return default

    @field_validator("status_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_status_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return cls._convert_enum_value(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )

    @field_validator(
        "birthdate",
        "moved_time",
        "last_activity_time",
        "mgo_cc_create",
        "mgo_cc_end",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_datetime_fields(cls, v: Any) -> Optional[datetime]:
        """Обрабатывает пустые значения для полей даты/времени"""
        if v is None or v == "":
            return None
        return v  # type: ignore[no-any-return]

    @field_validator(
        "last_communication_time",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        """Парсит строковые даты в формате 'dd.mm.YYYY HH:MM:SS'"""
        if not v:
            return None

        # Если значение уже является datetime
        if isinstance(v, datetime):
            return v

        # Если пришла строка в ISO формате
        if "T" in v or "-" in v:
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                pass

        # Обработка кастомного формата "dd.mm.YYYY HH:MM:SS"
        try:
            return datetime.strptime(v, "%d.%m.%Y %H:%M:%S")
        except (ValueError, TypeError):
            pass

        # Для других форматов используем стандартный парсер
        try:
            return datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError(f"Неверный формат даты: {v}")


class LeadUpdate(BaseUpdateSchema):
    """Модель для частичного обновления сделок"""

    # Основные поля с алиасами (все необязательные)
    # external_id: Optional[int] = Field(None, alias="ID")
    title: Optional[str] = Field(None, alias="TITLE")
    comments: Optional[str] = Field(None, alias="COMMENTS")
    name: Optional[str] = Field(None, alias="NAME")
    second_name: Optional[str] = Field(None, alias="SECOND_NAME")
    last_name: Optional[str] = Field(None, alias="LAST_NAME")
    post: Optional[str] = Field(None, alias="POST")
    company_title: Optional[str] = Field(None, alias="COMPANY_TITLE")

    # Статусы и флаги
    is_manual_opportunity: Optional[bool] = Field(
        None, alias="IS_MANUAL_OPPORTUNITY"
    )
    opened: Optional[bool] = Field(None, alias="OPENED")
    is_return_customer: Optional[bool] = Field(
        None, alias="IS_RETURN_CUSTOMER"
    )
    is_shipment_approved: Optional[bool] = Field(
        None, alias="UF_CRM_1623830089"
    )
    has_phone: Optional[bool] = Field(None, alias="HAS_PHONE")
    has_email: Optional[bool] = Field(None, alias="HAS_EMAIL")
    has_imol: Optional[bool] = Field(None, alias="HAS_IMOL")

    # Финансовые данные
    opportunity: Optional[float] = Field(None, alias="OPPORTUNITY")

    # Временные метки
    birthdate: Optional[datetime] = Field(None, alias="BIRTHDATE")
    date_closed: Optional[datetime] = Field(None, alias="DATE_CLOSED")
    date_create: Optional[datetime] = Field(None, alias="DATE_CREATE")
    date_modify: Optional[datetime] = Field(None, alias="DATE_MODIFY")
    moved_time: Optional[datetime] = Field(None, alias="MOVED_TIME")
    last_activity_time: Optional[datetime] = Field(
        None, alias="LAST_ACTIVITY_TIME"
    )
    last_communication_time: Optional[datetime] = Field(
        None, alias="LAST_COMMUNICATION_TIME"
    )

    # География и источники
    city: Optional[str] = Field(None, alias="UF_CRM_DCT_CITY")
    source_description: Optional[str] = Field(None, alias="SOURCE_DESCRIPTION")
    status_description: Optional[str] = Field(None, alias="STATUS_DESCRIPTION")
    source_external: Optional[str] = Field(None, alias="UF_CRM_DCT_SOURCE")
    originator_id: Optional[str] = Field(None, alias="ORIGINATOR_ID")
    origin_id: Optional[str] = Field(None, alias="ORIGIN_ID")

    # Адрес
    address: Optional[str] = Field(None, alias="ADDRESS")
    address_2: Optional[str] = Field(None, alias="ADDRESS_2")
    address_city: Optional[str] = Field(None, alias="ADDRESS_CITY")
    address_postal_code: Optional[str] = Field(
        None, alias="ADDRESS_POSTAL_CODE"
    )
    address_region: Optional[str] = Field(None, alias="ADDRESS_REGION")
    address_province: Optional[str] = Field(None, alias="ADDRESS_PROVINCE")
    address_country: Optional[str] = Field(None, alias="ADDRESS_COUNTRY")
    address_country_code: Optional[str] = Field(
        None, alias="ADDRESS_COUNTRY_CODE"
    )
    address_loc_addr_id: Optional[int] = Field(
        None, alias="ADDRESS_LOC_ADDR_ID"
    )

    # Перечисляемые типы
    status_semantic_id: Optional[StageSemanticEnum] = Field(
        None, alias="STATUS_SEMANTIC_ID"
    )

    # Связи с другими сущностями
    currency_id: Optional[str] = Field(None, alias="CURRENCY_ID")
    type_id: Optional[str] = Field(None, alias="UF_CRM_1629271075")
    status_id: Optional[str] = Field(None, alias="STATUS_ID")
    company_id: Optional[int] = Field(None, alias="COMPANY_ID")
    contact_id: Optional[int] = Field(None, alias="CONTACT_ID")
    source_id: Optional[str] = Field(None, alias="SOURCE_ID")
    main_activity_id: Optional[int] = Field(None, alias="UF_CRM_1598882174")
    deal_failure_reason_id: Optional[int] = Field(
        None, alias="UF_CRM_1697036607"
    )

    # Связи по пользователю
    assigned_by_id: Optional[int] = Field(None, alias="ASSIGNED_BY_ID")
    created_by_id: Optional[int] = Field(None, alias="CREATED_BY_ID")
    modify_by_id: Optional[int] = Field(None, alias="MODIFY_BY_ID")
    moved_by_id: Optional[int] = Field(None, alias="MOVED_BY_ID")
    last_activity_by: Optional[int] = Field(None, alias="LAST_ACTIVITY_BY")

    # Маркетинговые метки
    utm_source: Optional[str] = Field(None, alias="UTM_SOURCE")
    utm_medium: Optional[str] = Field(None, alias="UTM_MEDIUM")
    utm_campaign: Optional[str] = Field(None, alias="UTM_CAMPAIGN")
    utm_content: Optional[str] = Field(None, alias="UTM_CONTENT")
    utm_term: Optional[str] = Field(None, alias="UTM_TERM")
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
        None, alias="UF_CRM_CALLTOUCHT413"
    )
    calltouch_call_id: Optional[str] = Field(
        None, alias="UF_CRM_CALLTOUCH3ZFT"
    )
    calltouch_request_id: Optional[str] = Field(
        None, alias="UF_CRM_CALLTOUCHWG9P"
    )
    yaclientid: Optional[str] = Field(None, alias="UF_CRM_1739432591418")

    # Социальные профили
    wz_instagram: Optional[str] = Field(None, alias="UF_CRM_INSTAGRAM_WZ")
    wz_vc: Optional[str] = Field(None, alias="UF_CRM_VK_WZ")
    wz_telegram_username: Optional[str] = Field(
        None, alias="UF_CRM_TELEGRAMUSERNAME_WZ"
    )
    wz_telegram_id: Optional[str] = Field(None, alias="UF_CRM_TELEGRAMID_WZ")
    wz_avito: Optional[str] = Field(None, alias="UF_CRM_AVITO_WZ")

    # Коммуникации
    phone: Optional[list[CommunicationChannel] | None] = Field(
        None, alias="PHONE"
    )
    email: Optional[list[CommunicationChannel] | None] = Field(
        None, alias="EMAIL"
    )
    web: Optional[list[CommunicationChannel] | None] = Field(None, alias="WEB")
    im: Optional[list[CommunicationChannel] | None] = Field(None, alias="IM")
    link: Optional[list[CommunicationChannel] | None] = Field(
        None, alias="LINK"
    )

    # Универсальный валидатор для всех полей
    @model_validator(mode="before")  # type: ignore[misc]
    @classmethod
    def normalize_empty_values(cls, data: Any) -> Any:
        """Преобразует пустые строки в None для всех полей"""
        if not isinstance(data, dict):
            return data

        for field in list(data.keys()):
            value = data[field]
            if isinstance(value, str) and value.strip() == "":
                data[field] = None
        return data

    # Валидаторы для преобразования значений
    @field_validator(
        "opened",
        "is_return_customer",
        "is_manual_opportunity",
        "is_shipment_approved",
        "has_phone",
        "has_email",
        "has_imol",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def convert_to_bool(cls, v: Any) -> bool:
        """Преобразует различные форматы в булевы значения"""
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.upper() in ("Y", "1", "TRUE", "T", "YES")
        if isinstance(v, int):
            return bool(v)
        return False

    @field_validator(
        "contact_id",
        "main_activity_id",
        "deal_failure_reason_id",
        "assigned_by_id",
        "created_by_id",
        "modify_by_id",
        "moved_by_id",
        "last_activity_by",
        "address_loc_addr_id",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_numeric_fields(cls, v: Any) -> Optional[int]:
        """Обрабатывает числовые поля: пустые значения → None, строки → int"""
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator(
        "opportunity",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_float_fields(cls, v: Any) -> Optional[float]:
        """
        Обрабатывает числовые поля: пустые значения → None, строки → float
        """
        if v is None or v == "":
            return None
        try:
            # v = ''.join(v.split())
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator(
        "company_id",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_company_id_fields(cls, v: Any) -> Optional[int]:
        """Обрабатывает числовые поля: 0 → None, строки → int"""
        if v is None or v == "" or v == "0":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _convert_enum_value(
        cls, v: Any, enum_type: Type[EnumT], default: EnumT
    ) -> EnumT:
        """Вспомогательная функция для преобразования значений enum"""
        if v is None or v == "":
            return default

        try:
            # Пробуем преобразовать строку в число
            if isinstance(v, str) and v.isdigit():
                v = int(v)

            # Пробуем найти значение в enum
            return enum_type(v)
        except (ValueError, TypeError):
            return default

    @field_validator("status_semantic_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_status_semantic_id(cls, v: Any) -> StageSemanticEnum:
        return cls._convert_enum_value(
            v, StageSemanticEnum, StageSemanticEnum.PROSPECTIVE
        )

    @field_validator(
        "birthdate",
        "moved_time",
        "last_activity_time",
        "mgo_cc_create",
        "mgo_cc_end",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_datetime_fields(cls, v: Any) -> Optional[datetime]:
        """Обрабатывает пустые значения для полей даты/времени"""
        if v is None or v == "":
            return None
        return v  # type: ignore[no-any-return]

    @field_validator(
        "last_communication_time",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        """Парсит строковые даты в формате 'dd.mm.YYYY HH:MM:SS'"""
        if not v:
            return None

        # Если значение уже является datetime
        if isinstance(v, datetime):
            return v

        # Если пришла строка в ISO формате
        if "T" in v or "-" in v:
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                pass

        # Обработка кастомного формата "dd.mm.YYYY HH:MM:SS"
        try:
            return datetime.strptime(v, "%d.%m.%Y %H:%M:%S")
        except (ValueError, TypeError):
            pass

        # Для других форматов используем стандартный парсер
        try:
            return datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError(f"Неверный формат даты: {v}")


# class LeadListResponse(BaseModel):  # type: ignore[misc]
#    """Схема для ответа со списком сделок"""

#    result: list[LeadUpdate]
#    next: int | None = None
#    total: int

#  model_config = ConfigDict(from_attributes=True)
#    model_config = ConfigDict(
#        use_enum_values=True,
#        populate_by_name=True,
#        arbitrary_types_allowed=True,
#        extra="ignore",
#    )
