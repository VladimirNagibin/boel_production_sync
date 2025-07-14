from datetime import datetime
from enum import Enum
from typing import Any, Generic, Optional, Type, TypeVar, cast
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

EnumT = TypeVar("EnumT", bound=Enum)
T = TypeVar("T")


class BaseFieldMixin:
    id: Optional[UUID] = Field(None)
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)
    is_deleted_in_bitrix: Optional[bool] = Field(None)

    comments: Optional[str] = Field(None, alias="COMMENTS")
    source_description: Optional[str] = Field(None, alias="SOURCE_DESCRIPTION")
    originator_id: Optional[str] = Field(None, alias="ORIGINATOR_ID")
    origin_id: Optional[str] = Field(None, alias="ORIGIN_ID")

    @model_validator(mode="before")  # type: ignore[misc]
    @classmethod
    def preprocess_data(cls, data: Any) -> Any:
        return BitrixValidators.normalize_empty_values(data)


class TimestampsCreateMixin:
    """Миксин для временных меток"""

    date_create: datetime = Field(..., alias="DATE_CREATE")
    date_modify: datetime = Field(..., alias="DATE_MODIFY")
    last_activity_time: Optional[datetime] = Field(
        None, alias="LAST_ACTIVITY_TIME"
    )
    last_communication_time: Optional[datetime] = Field(
        None, alias="LAST_COMMUNICATION_TIME"
    )

    @field_validator(
        "last_communication_time",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def validate_datetime_format(cls, v: Any) -> Optional[datetime]:
        return BitrixValidators.parse_datetime(v)


class TimestampsUpdateMixin:
    """Миксин для временных меток"""

    date_create: Optional[datetime] = Field(None, alias="DATE_CREATE")
    date_modify: Optional[datetime] = Field(None, alias="DATE_MODIFY")
    last_activity_time: Optional[datetime] = Field(
        None, alias="LAST_ACTIVITY_TIME"
    )
    last_communication_time: Optional[datetime] = Field(
        None, alias="LAST_COMMUNICATION_TIME"
    )

    @field_validator(
        "last_communication_time",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def validate_datetime_format(cls, v: Any) -> Optional[datetime]:
        return BitrixValidators.parse_datetime(v)


class UserRelationsCreateMixin:
    """Миксин связанных пользователей"""

    assigned_by_id: int = Field(..., alias="ASSIGNED_BY_ID")
    created_by_id: int = Field(..., alias="CREATED_BY_ID")
    modify_by_id: int = Field(..., alias="MODIFY_BY_ID")
    last_activity_by: Optional[int] = Field(None, alias="LAST_ACTIVITY_BY")


class UserRelationsUpdateMixin:
    assigned_by_id: Optional[int] = Field(None, alias="ASSIGNED_BY_ID")
    created_by_id: Optional[int] = Field(None, alias="CREATED_BY_ID")
    modify_by_id: Optional[int] = Field(None, alias="MODIFY_BY_ID")
    last_activity_by: Optional[int] = Field(None, alias="LAST_ACTIVITY_BY")


class MarketingMixin:
    """Миксин для маркетинговых полей"""

    utm_source: Optional[str] = Field(None, alias="UTM_SOURCE")
    utm_medium: Optional[str] = Field(None, alias="UTM_MEDIUM")
    utm_campaign: Optional[str] = Field(None, alias="UTM_CAMPAIGN")
    utm_content: Optional[str] = Field(None, alias="UTM_CONTENT")
    utm_term: Optional[str] = Field(None, alias="UTM_TERM")


class AddressMixin:
    """Миксин для адресных полей"""

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


class HasCommunicationCreateMixin:
    """Присутствуют коммуникации"""

    has_phone: bool = Field(..., alias="HAS_PHONE")
    has_email: bool = Field(..., alias="HAS_EMAIL")
    has_imol: bool = Field(..., alias="HAS_IMOL")


class HasCommunicationUpdateMixin:
    """Присутствуют коммуникации"""

    has_phone: Optional[bool] = Field(None, alias="HAS_PHONE")
    has_email: Optional[bool] = Field(None, alias="HAS_EMAIL")
    has_imol: Optional[bool] = Field(None, alias="HAS_IMOL")


class BaseCreateSchema(
    BaseFieldMixin,
    TimestampsCreateMixin,
    UserRelationsCreateMixin,
    MarketingMixin,
    BaseModel,  # type: ignore[misc]
):
    """Базовая схема для создания сущностей"""

    external_id: int = Field(..., alias="ID")
    opened: bool = Field(True, alias="OPENED")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class BaseUpdateSchema(
    BaseFieldMixin,
    TimestampsUpdateMixin,
    UserRelationsUpdateMixin,
    MarketingMixin,
    BaseModel,  # type: ignore[misc]
):
    """Базовая схема для обновления сущностей"""

    external_id: Optional[int] = Field(None, alias="ID")
    opened: Optional[bool] = Field(None, alias="OPENED")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    def to_bitrix_dict(self) -> dict[str, Any]:
        """Преобразует модель в словарь для Bitrix API"""
        data = self.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,  # опционально: исключить неустановленные поля
        )

        # Дополнительные преобразования
        result: dict[str, Any] = {}
        for alias, value in data.items():
            if isinstance(value, bool):
                if alias in (
                    "UF_CRM_60D2AFAEB32CC",
                    "UF_CRM_1632738559",
                    "UF_CRM_1623830089",
                    "UF_CRM_60D97EF75E465",
                    "UF_CRM_61974C16DBFBF",
                ):
                    result[alias] = "1" if value else "0"
                else:
                    # Булёвы значения -> "Y"/"N"
                    result[alias] = "Y" if value else "N"
            elif isinstance(value, datetime):
                # Особый формат для last_communication_time
                if alias == "LAST_COMMUNICATION_TIME":
                    result[alias] = value.strftime("%d.%m.%Y %H:%M:%S")
                # Стандартный ISO формат для остальных дат
                else:
                    iso_format = value.strftime("%Y-%m-%dT%H:%M:%S%z")
                    if iso_format and iso_format[-5] in ("+", "-"):
                        iso_format = f"{iso_format[:-2]}:{iso_format[-2:]}"
                    result[alias] = iso_format
            elif alias == "ID":
                continue
            else:
                # Остальные значения без изменений
                result[alias] = value
        return result


class ListResponseSchema(BaseModel, Generic[T]):  # type: ignore[misc]
    """Схема для ответа со списком сущностей"""

    result: list[T]
    total: int
    next: Optional[int] = None

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


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


class BitrixValidators:
    """Класс с общими валидаторами для Bitrix схем"""

    @staticmethod
    def normalize_empty_values(data: Any) -> Any:
        """Преобразует пустые строки в None для всех полей"""
        if not isinstance(data, dict):
            return data

        processed_data: dict[str, Any] = cast(dict[str, Any], data)

        for field in list(processed_data.keys()):
            value = processed_data[field]
            if isinstance(value, str) and value.strip() == "":
                processed_data[field] = None
        return processed_data

    @staticmethod
    def convert_to_bool(v: Any) -> bool:
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

    @staticmethod
    def normalize_int(v: Any) -> Optional[int]:
        """Обрабатывает числовые поля: пустые значения → None, строки → int"""
        if v in (None, "", "0"):
            return None
        try:
            # v = ''.join(v.split())
            return int(v)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def normalize_float(v: Any) -> Optional[float]:
        """Обрабатывает числовые поля: пустые значения → None, строки → int"""
        if v in (None, ""):
            return None
        try:
            # v = ''.join(v.split())
            return float(v)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def normalize_datetime_fields(v: Any) -> Optional[datetime]:
        """Обрабатывает пустые значения для полей даты/времени"""
        if v is None or v == "":
            return None
        return v  # type: ignore[no-any-return]

    @staticmethod
    def parse_datetime(v: Any) -> Optional[datetime]:
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

    @staticmethod
    def convert_enum(v: Any, enum_type: Type[EnumT], default: EnumT) -> EnumT:
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

    @staticmethod
    def normalize_list(v: Any) -> list[Any]:
        """Проверяет списки"""
        if v is None:
            return []
        # Если значение уже является list
        if isinstance(v, list):
            return v
        return []
