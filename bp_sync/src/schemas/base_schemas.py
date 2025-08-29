from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Generic, Optional, Type, TypeVar, cast
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from typing_extensions import Self

from models.enums import DualTypePaymentEnum, DualTypeShipmentEnum

from .fields import FIELDS_BY_TYPE, FIELDS_BY_TYPE_ALT

EnumT = TypeVar("EnumT", bound=Enum)
T = TypeVar("T")
SYSTEM_USER_ID = 1


class CommonFieldMixin(BaseModel):  # type: ignore[misc]
    internal_id: Optional[UUID] = Field(
        default=None,
        # alias="id",
        exclude=True,
        init_var=False,
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    is_deleted_in_bitrix: Optional[bool] = Field(default=None)

    external_id: Optional[int | str] = Field(
        None,
        validation_alias=AliasChoices("ID", "id"),
    )

    @property
    def id(self) -> Optional[UUID]:
        return self.internal_id

    @id.setter
    def id(self, value: UUID) -> None:
        self.internal_id = value

    def get_changes(
        self, entity: Self, exclude_fields: set[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        if exclude_fields is None:
            exclude_fields = {
                "internal_id",
                "created_at",
                "updated_at",
                "is_deleted_in_bitrix",
                "parent_deal_id",
            }

        differences: dict[str, dict[str, Any]] = {}

        model_class = self.__class__
        fields = model_class.model_fields

        for field_name in fields:
            # Пропускаем исключенные поля
            if field_name in exclude_fields:
                continue

            old_value = getattr(self, field_name)
            new_value = getattr(entity, field_name)

            # Сравниваем значения
            if not self._are_values_equal(field_name, old_value, new_value):
                differences[field_name] = {
                    "internal": old_value,
                    "external": new_value,
                }

        return differences

    def _are_values_equal(
        self, field_name: str, value1: Any, value2: Any
    ) -> bool:
        """
        Сравнивает два значения с учетом специальных типов данных.
        """
        # Оба значения None
        if value1 is None and value2 is None:
            return True

        if field_name == "company_id":
            if value1 in (0, None) and value2 in (0, None):
                return True

        if field_name in ("defects", "related_deals"):
            if value1 in ([], None) and value2 in ([], None):
                return True
            return False

        # Одно из значений None
        if value1 is None or value2 is None:
            return False

        # Для дат и времени сравниваем как строки в ISO формате
        # if isinstance(value1, (datetime, date)) and isinstance(
        #    value2, (datetime, date)
        # ):
        #    return value1.isoformat() == value2.isoformat()

        # Для Enum сравниваем значения
        if hasattr(value1, "value") and hasattr(value2, "value"):
            return bool(value1.value == value2.value)

        # Для Pydantic моделей рекурсивно сравниваем все поля
        if isinstance(value1, BaseModel) and isinstance(value2, BaseModel):
            return bool(value1.model_dump() == value2.model_dump())

        # Для списков и словарей сравниваем содержимое
        if isinstance(value1, (list, dict)) and isinstance(
            value2, (list, dict)
        ):
            return bool(value1 == value2)

        # Стандартное сравнение
        return bool(value1 == value2)


class BaseFieldMixin:
    comments: Optional[str] = Field(None, alias="COMMENTS")
    source_description: Optional[str] = Field(None, alias="SOURCE_DESCRIPTION")
    originator_id: Optional[str] = Field(None, alias="ORIGINATOR_ID")
    origin_id: Optional[str] = Field(None, alias="ORIGIN_ID")


class TimestampsCreateMixin:
    """Миксин для временных меток"""

    date_create: datetime = Field(
        ...,
        validation_alias=AliasChoices("DATE_CREATE", "createdTime"),
    )
    date_modify: datetime = Field(
        ...,
        validation_alias=AliasChoices("DATE_MODIFY", "updatedTime"),
    )
    last_activity_time: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices(
            "LAST_ACTIVITY_TIME", "lastActivityTime"
        ),
    )
    last_communication_time: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices(
            "LAST_COMMUNICATION_TIME", "lastCommunicationTime"
        ),
    )


class TimestampsUpdateMixin:
    """Миксин для временных меток"""

    date_create: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("DATE_CREATE", "createdTime"),
    )
    date_modify: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("DATE_MODIFY", "updatedTime"),
    )
    last_activity_time: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices(
            "LAST_ACTIVITY_TIME", "lastActivityTime"
        ),
    )
    last_communication_time: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices(
            "LAST_COMMUNICATION_TIME", "lastCommunicationTime"
        ),
    )


class UserRelationsCreateMixin:
    """Миксин связанных пользователей"""

    assigned_by_id: int = Field(
        ...,
        validation_alias=AliasChoices("ASSIGNED_BY_ID", "assignedById"),
    )
    created_by_id: int = Field(
        ...,
        validation_alias=AliasChoices("CREATED_BY_ID", "createdBy"),
    )
    modify_by_id: int = Field(
        ...,
        validation_alias=AliasChoices("MODIFY_BY_ID", "updatedBy"),
    )
    last_activity_by: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("LAST_ACTIVITY_BY", "lastActivityBy"),
    )


class UserRelationsUpdateMixin:
    assigned_by_id: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("ASSIGNED_BY_ID", "assignedById"),
    )
    created_by_id: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("CREATED_BY_ID", "createdBy"),
    )
    modify_by_id: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("MODIFY_BY_ID", "updatedBy"),
    )
    last_activity_by: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("LAST_ACTIVITY_BY", "lastActivityBy"),
    )


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


class EntityAwareSchema(BaseModel):  # type: ignore[misc]
    FIELDS_BY_TYPE: ClassVar[dict[str, Any]] = FIELDS_BY_TYPE
    FIELDS_BY_TYPE_ALT: ClassVar[dict[str, Any]] = FIELDS_BY_TYPE_ALT

    @model_validator(mode="before")  # type: ignore[misc]
    @classmethod
    def preprocess_data(cls, data: Any) -> Any:
        return BitrixValidators.normalize_empty_values(
            data, fields=cls.FIELDS_BY_TYPE
        )

    def model_dump_db(self, exclude_unset: bool = False) -> dict[str, Any]:

        data = self.model_dump(exclude_unset=exclude_unset)
        for key in self.FIELDS_BY_TYPE_ALT["list"]:
            try:
                del data[key]
            except KeyError:
                ...
        for key, value in data.items():
            if (
                (key in self.FIELDS_BY_TYPE_ALT["str_none"] and not value)
                or key == "parent_deal_id"
                or key == "parent_company_id"
            ):
                data[key] = None
            elif key in self.FIELDS_BY_TYPE_ALT["int_none"] and (
                value is None or not int(value)
            ):
                data[key] = None
            elif key == "shipment_type":
                data[key] = DualTypeShipmentEnum(value)
            elif key == "payment_type":
                data[key] = DualTypePaymentEnum(value)
        return data  # type: ignore[no-any-return]


class CoreCreateSchema(
    CommonFieldMixin,
    TimestampsCreateMixin,
    UserRelationsCreateMixin,
    EntityAwareSchema,
):
    """Базовая схема для создания сущностей"""

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class BaseCreateSchema(
    CoreCreateSchema,
    BaseFieldMixin,
    MarketingMixin,
):
    """Базовая схема для создания сущностей"""

    opened: bool = Field(default=True, alias="OPENED")


class CoreUpdateSchema(
    CommonFieldMixin,
    TimestampsUpdateMixin,
    UserRelationsUpdateMixin,
    BaseModel,  # type: ignore[misc]
):
    """Базовая схема для обновления сущностей"""

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
                elif alias == "webformId":
                    result[alias] = 1 if value else 0
                else:
                    # Булёвы значения -> "Y"/"N"
                    result[alias] = "Y" if value else "N"
            elif isinstance(value, datetime):
                # Особый формат для last_communication_time
                if alias in (
                    "LAST_COMMUNICATION_TIME",
                    "lastCommunicationTime",
                ):
                    result[alias] = value.strftime("%d.%m.%Y %H:%M:%S")
                # Стандартный ISO формат для остальных дат
                else:
                    iso_format = value.strftime("%Y-%m-%dT%H:%M:%S%z")
                    if iso_format and iso_format[-5] in ("+", "-"):
                        iso_format = f"{iso_format[:-2]}:{iso_format[-2:]}"
                    result[alias] = iso_format
            elif alias in (
                FIELDS_BY_TYPE["int_none"] + FIELDS_BY_TYPE["enums"]
            ):
                result[alias] = "" if value == 0 else value
            elif alias == "ID":
                continue
            else:
                # Остальные значения без изменений (проверка ссылочных полей)
                result[alias] = value
        return result


class BaseUpdateSchema(
    CoreUpdateSchema,
    BaseFieldMixin,
    MarketingMixin,
):
    """Базовая схема для обновления сущностей"""

    opened: Optional[bool] = Field(default=None, alias="OPENED")


class ListResponseSchema(BaseModel, Generic[T]):  # type: ignore[misc]
    """Схема для ответа со списком сущностей"""

    result: list[CommonFieldMixin]  # list[T]
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
    def normalize_empty_values(data: Any, fields: dict[str, Any]) -> Any:
        """Преобразует пустые строки в None для всех полей"""
        if not isinstance(data, dict):
            return data
        processed_data: dict[str, Any] = cast(dict[str, Any], data)
        for field in list(processed_data.keys()):
            value = processed_data[field]
            # print(f"{field}::{value}")
            if field == "id":
                processed_data["ID"] = processed_data.pop("id")
            elif field in (
                "CREATED_BY_ID",
                "created_by_id",
                "MODIFY_BY_ID",
                "modify_by_id",
                "updatedBy",
            ):
                processed_data[field] = (
                    value
                    if (int(value) and int(value) != 8971)
                    else SYSTEM_USER_ID
                )
            elif field in fields.get("str_none", []) and not value:
                processed_data[field] = None
            elif field in fields.get("int_none", []) and not value:
                processed_data[field] = None  # 0
            elif field in (
                fields.get("bool", []) + fields.get("bool_none", [])
            ):
                processed_data[field] = bool(value in ("Y", "1", 1, True))
            elif field in (
                fields.get("datetime", []) + fields.get("datetime_none", [])
            ):
                processed_data[field] = BitrixValidators.parse_datetime(value)
            elif field in fields.get("float", []):
                processed_data[field] = BitrixValidators.normalize_float(value)
            elif field in fields.get("list", []):
                processed_data[field] = BitrixValidators.normalize_list(value)
            elif field in fields.get("list_in_int", []):
                processed_data[field] = BitrixValidators.list_in_int(value)
            elif field in fields.get("dict_none", []):
                if value:
                    processed_data[field] = value["value"]
        return processed_data

    @staticmethod
    def normalize_float(v: Any) -> Optional[float]:
        "Обрабатывает числовые поля: пустые значения → None, строки → int"
        if v in (None, ""):
            return 0
        try:
            # v = ''.join(v.split())
            return float(v)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def parse_datetime(v: Any) -> datetime | None:
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

    @staticmethod
    def list_in_int(v: Any) -> int:
        """Первое значение из списка"""
        if v is None:
            return 0
        # Если значение уже является list
        if isinstance(v, list) and v:
            return int(v[0])
        return 0
