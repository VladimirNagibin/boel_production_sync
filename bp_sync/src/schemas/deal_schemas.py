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

from models.enums import (
    ProcessingStatusEnum,
    StageSemanticEnum,
    TypePaymentEnum,
    TypeShipmentEnum,
)

EnumT = TypeVar("EnumT", bound=Enum)


class DealCreate(BaseModel):  # type: ignore[misc]
    # Поля с алиасами для соответствия SQLAlchemy модели

    # Идентификаторы и основные данные
    external_id: int = Field(..., alias="ID")
    title: str = Field(..., alias="TITLE")
    comments: Optional[str] = Field(None, alias="COMMENTS")
    additional_info: Optional[str] = Field(None, alias="ADDITIONAL_INFO")

    # Статусы и флаги
    probability: Optional[int] = Field(None, alias="PROBABILITY")
    is_manual_opportunity: bool = Field(False, alias="IS_MANUAL_OPPORTUNITY")
    opened: bool = Field(True, alias="OPENED")
    closed: bool = Field(False, alias="CLOSED")
    is_new: bool = Field(False, alias="IS_NEW")
    is_recurring: bool = Field(False, alias="IS_RECURRING")
    is_return_customer: bool = Field(False, alias="IS_RETURN_CUSTOMER")
    is_repeated_approach: bool = Field(False, alias="IS_REPEATED_APPROACH")
    is_shipment_approved: Optional[bool] = Field(
        None, alias="UF_CRM_60D2AFAEB32CC"
    )
    is_shipment_approved_invoice: Optional[bool] = Field(
        None, alias="UF_CRM_1632738559"
    )

    # Финансовые данные
    opportunity: float = Field(0.0, alias="OPPORTUNITY")
    payment_grace_period: Optional[int] = Field(
        None, alias="UF_CRM_1656582798"
    )

    # Временные метки
    begindate: datetime = Field(..., alias="BEGINDATE")
    closedate: datetime = Field(..., alias="CLOSEDATE")
    date_create: datetime = Field(..., alias="DATE_CREATE")
    date_modify: datetime = Field(..., alias="DATE_MODIFY")
    moved_time: Optional[datetime] = Field(None, alias="MOVED_TIME")
    last_activity_time: Optional[datetime] = Field(
        None, alias="LAST_ACTIVITY_TIME"
    )
    last_communication_time: Optional[datetime] = Field(
        None, alias="LAST_COMMUNICATION_TIME"
    )
    payment_deadline: Optional[datetime] = Field(
        None, alias="UF_CRM_1632738230"
    )

    # География и источники
    city: Optional[str] = Field(None, alias="UF_CRM_DCT_CITY")
    source_description: Optional[str] = Field(None, alias="SOURCE_DESCRIPTION")
    source_external: Optional[str] = Field(None, alias="UF_CRM_DCT_SOURCE")
    originator_id: Optional[str] = Field(None, alias="ORIGINATOR_ID")
    origin_id: Optional[str] = Field(None, alias="ORIGIN_ID")
    id_printed_form: Optional[str] = Field(None, alias="UF_CRM_1656227383")

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
    currency_id: Optional[str] = Field(None, alias="CURRENCY_ID")
    type_id: Optional[str] = Field(None, alias="TYPE_ID")
    stage_id: str = Field(..., alias="STAGE_ID")
    lead_id: Optional[int] = Field(None, alias="LEAD_ID")
    company_id: Optional[int] = Field(None, alias="COMPANY_ID")
    contact_id: Optional[int] = Field(None, alias="CONTACT_ID")
    category_id: int = Field(..., alias="CATEGORY_ID")
    source_id: Optional[str] = Field(None, alias="SOURCE_ID")
    main_activity_id: Optional[int] = Field(None, alias="UF_CRM_1598883361")
    lead_type_id: Optional[str] = Field(None, alias="UF_CRM_612463720554B")
    invoice_stage_id: Optional[str] = Field(None, alias="UF_CRM_1632738354")
    current_stage_id: Optional[str] = Field(None, alias="UF_CRM_1632738604")
    shipping_company_id: Optional[int] = Field(None, alias="UF_CRM_1650617036")
    creation_source_id: Optional[int] = Field(None, alias="UF_CRM_1654577096")
    warehouse_id: Optional[int] = Field(None, alias="UF_CRM_1659326670")

    # Связи по пользователю
    assigned_by_id: int = Field(..., alias="ASSIGNED_BY_ID")
    created_by_id: int = Field(..., alias="CREATED_BY_ID")
    modify_by_id: int = Field(..., alias="MODIFY_BY_ID")
    moved_by_id: Optional[int] = Field(None, alias="MOVED_BY_ID")
    last_activity_by: Optional[int] = Field(None, alias="LAST_ACTIVITY_BY")
    defect_expert_id: Optional[int] = Field(None, alias="UF_CRM_1655618547")

    # Поля сервисных сделок
    defect_conclusion: Optional[str] = Field(
        None, alias="UF_CRM_1655618110493"
    )

    # Связанные сделки (доставка)
    parent_deal_id: Optional[int] = Field(None, alias="UF_CRM_1655891443")

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
        "closed",
        "is_new",
        "is_recurring",
        "is_return_customer",
        "is_repeated_approach",
        "is_manual_opportunity",
        "is_shipment_approved",
        "is_shipment_approved_invoice",
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
        "probability",
        "payment_grace_period",
        "lead_id",
        "company_id",
        "contact_id",
        "main_activity_id",
        "shipping_company_id",
        "creation_source_id",
        "warehouse_id",
        "assigned_by_id",
        "created_by_id",
        "modify_by_id",
        "moved_by_id",
        "last_activity_by",
        "defect_expert_id",
        "parent_deal_id",
        "category_id",
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

    @field_validator("payment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_type(cls, v: Any) -> TypePaymentEnum:
        return cls._convert_enum_value(
            v, TypePaymentEnum, TypePaymentEnum.NOT_DEFINE
        )

    @field_validator("shipping_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_shipping_type(cls, v: Any) -> TypeShipmentEnum:
        return cls._convert_enum_value(
            v, TypeShipmentEnum, TypeShipmentEnum.NOT_DEFINE
        )

    @field_validator("processing_status", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_processing_status(cls, v: Any) -> ProcessingStatusEnum:
        return cls._convert_enum_value(
            v, ProcessingStatusEnum, ProcessingStatusEnum.NOT_DEFINE
        )

    @field_validator(
        "payment_deadline",
        "moved_time",
        "last_activity_time",
        # "last_communication_time",
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

    @field_validator("probability", mode="before")  # type: ignore[misc]
    @classmethod
    def validate_probability(cls, v: Any) -> Optional[int]:
        """Валидация и нормализация вероятности"""
        if v in ("", None):
            return None
        try:
            value = int(v)
            if 0 <= value <= 100:
                return value
            return None
        except (ValueError, TypeError):
            return None

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class DealUpdate(BaseModel):  # type: ignore[misc]
    """Модель для частичного обновления сделок"""

    # Основные поля с алиасами (все необязательные)
    external_id: Optional[int] = Field(None, alias="ID")
    title: Optional[str] = Field(None, alias="TITLE")
    comments: Optional[str] = Field(None, alias="COMMENTS")
    additional_info: Optional[str] = Field(None, alias="ADDITIONAL_INFO")

    # Статусы и флаги
    probability: Optional[int] = Field(None, alias="PROBABILITY")
    is_manual_opportunity: Optional[bool] = Field(
        None, alias="IS_MANUAL_OPPORTUNITY"
    )
    opened: Optional[bool] = Field(None, alias="OPENED")
    closed: Optional[bool] = Field(None, alias="CLOSED")
    is_new: Optional[bool] = Field(None, alias="IS_NEW")
    is_recurring: Optional[bool] = Field(None, alias="IS_RECURRING")
    is_return_customer: Optional[bool] = Field(
        None, alias="IS_RETURN_CUSTOMER"
    )
    is_repeated_approach: Optional[bool] = Field(
        None, alias="IS_REPEATED_APPROACH"
    )
    is_shipment_approved: Optional[bool] = Field(
        None, alias="UF_CRM_60D2AFAEB32CC"
    )
    is_shipment_approved_invoice: Optional[bool] = Field(
        None, alias="UF_CRM_1632738559"
    )

    # Финансовые данные
    opportunity: Optional[float] = Field(None, alias="OPPORTUNITY")
    payment_grace_period: Optional[int] = Field(
        None, alias="UF_CRM_1656582798"
    )

    # Временные метки
    begindate: Optional[datetime] = Field(None, alias="BEGINDATE")
    closedate: Optional[datetime] = Field(None, alias="CLOSEDATE")
    date_create: Optional[datetime] = Field(None, alias="DATE_CREATE")
    date_modify: Optional[datetime] = Field(None, alias="DATE_MODIFY")
    moved_time: Optional[datetime] = Field(None, alias="MOVED_TIME")
    last_activity_time: Optional[datetime] = Field(
        None, alias="LAST_ACTIVITY_TIME"
    )
    last_communication_time: Optional[datetime] = Field(
        None, alias="LAST_COMMUNICATION_TIME"
    )
    payment_deadline: Optional[datetime] = Field(
        None, alias="UF_CRM_1632738230"
    )

    # География и источники
    city: Optional[str] = Field(None, alias="UF_CRM_DCT_CITY")
    source_description: Optional[str] = Field(None, alias="SOURCE_DESCRIPTION")
    source_external: Optional[str] = Field(None, alias="UF_CRM_DCT_SOURCE")
    originator_id: Optional[str] = Field(None, alias="ORIGINATOR_ID")
    origin_id: Optional[str] = Field(None, alias="ORIGIN_ID")
    id_printed_form: Optional[str] = Field(None, alias="UF_CRM_1656227383")

    # Перечисляемые типы
    stage_semantic_id: Optional[StageSemanticEnum] = Field(
        None, alias="STAGE_SEMANTIC_ID"
    )
    payment_type: Optional[TypePaymentEnum] = Field(
        None, alias="UF_CRM_1632738315"
    )
    shipping_type: Optional[TypeShipmentEnum] = Field(
        None, alias="UF_CRM_1655141630"
    )
    processing_status: Optional[ProcessingStatusEnum] = Field(
        None, alias="UF_CRM_1750571370"
    )

    # Связи с другими сущностями
    currency_id: Optional[str] = Field(None, alias="CURRENCY_ID")
    type_id: Optional[str] = Field(None, alias="TYPE_ID")
    stage_id: Optional[str] = Field(None, alias="STAGE_ID")
    lead_id: Optional[int] = Field(None, alias="LEAD_ID")
    company_id: Optional[int] = Field(None, alias="COMPANY_ID")
    contact_id: Optional[int] = Field(None, alias="CONTACT_ID")
    category_id: Optional[int] = Field(None, alias="CATEGORY_ID")
    source_id: Optional[str] = Field(None, alias="SOURCE_ID")
    main_activity_id: Optional[int] = Field(None, alias="UF_CRM_1598883361")
    lead_type_id: Optional[str] = Field(None, alias="UF_CRM_612463720554B")
    invoice_stage_id: Optional[str] = Field(None, alias="UF_CRM_1632738354")
    current_stage_id: Optional[str] = Field(None, alias="UF_CRM_1632738604")
    shipping_company_id: Optional[int] = Field(None, alias="UF_CRM_1650617036")
    creation_source_id: Optional[int] = Field(None, alias="UF_CRM_1654577096")
    warehouse_id: Optional[int] = Field(None, alias="UF_CRM_1659326670")

    # Связи по пользователю
    assigned_by_id: Optional[int] = Field(None, alias="ASSIGNED_BY_ID")
    created_by_id: Optional[int] = Field(None, alias="CREATED_BY_ID")
    modify_by_id: Optional[int] = Field(None, alias="MODIFY_BY_ID")
    moved_by_id: Optional[int] = Field(None, alias="MOVED_BY_ID")
    last_activity_by: Optional[int] = Field(None, alias="LAST_ACTIVITY_BY")
    defect_expert_id: Optional[int] = Field(None, alias="UF_CRM_1655618547")

    # Поля сервисных сделок
    defect_conclusion: Optional[str] = Field(
        None, alias="UF_CRM_1655618110493"
    )

    # Связанные сделки (доставка)
    parent_deal_id: Optional[int] = Field(None, alias="UF_CRM_1655891443")

    # Валидаторы (такие же как в DealCreate)
    @model_validator(mode="before")  # type: ignore[misc]
    @classmethod
    def normalize_empty_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for field in list(data.keys()):
            value = data[field]
            if isinstance(value, str) and value.strip() == "":
                data[field] = None
        return data

    @field_validator(
        "opened",
        "closed",
        "is_new",
        "is_recurring",
        "is_return_customer",
        "is_repeated_approach",
        "is_manual_opportunity",
        "is_shipment_approved",
        "is_shipment_approved_invoice",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def convert_to_bool(cls, v: Any) -> Optional[bool]:
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.upper() in ("Y", "1", "TRUE", "T", "YES")
        if isinstance(v, int):
            return bool(v)
        return None

    @field_validator(
        "probability",
        "payment_grace_period",
        "lead_id",
        "company_id",
        "contact_id",
        "main_activity_id",
        "shipping_company_id",
        "creation_source_id",
        "warehouse_id",
        "assigned_by_id",
        "created_by_id",
        "modify_by_id",
        "moved_by_id",
        "last_activity_by",
        "defect_expert_id",
        "parent_deal_id",
        "category_id",
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
        "payment_deadline",
        "moved_time",
        "last_activity_time",
        # "last_communication_time",
        mode="before",
    )  # type: ignore[misc]
    @classmethod
    def normalize_datetime_fields(cls, v: Any) -> Optional[datetime]:
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

    @field_validator("probability", mode="before")  # type: ignore[misc]
    @classmethod
    def validate_probability(cls, v: Any) -> Optional[int]:
        if v in ("", None):
            return None
        try:
            value = int(v)
            if 0 <= value <= 100:
                return value
            return None
        except (ValueError, TypeError):
            return None

    # Enum-валидаторы
    @classmethod
    def _convert_enum_value(
        cls, v: Any, enum_type: Type[EnumT], default: EnumT
    ) -> Optional[EnumT]:
        if v is None or v == "":
            return None
        try:
            if isinstance(v, str) and v.isdigit():
                v = int(v)
            return enum_type(v)
        except (ValueError, TypeError):
            return None

    @field_validator("payment_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_type(cls, v: Any) -> Optional[TypePaymentEnum]:
        return cls._convert_enum_value(
            v, TypePaymentEnum, TypePaymentEnum.NOT_DEFINE
        )

    @field_validator("shipping_type", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_shipping_type(cls, v: Any) -> Optional[TypeShipmentEnum]:
        return cls._convert_enum_value(
            v, TypeShipmentEnum, TypeShipmentEnum.NOT_DEFINE
        )

    @field_validator("processing_status", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_processing_status(
        cls, v: Any
    ) -> Optional[ProcessingStatusEnum]:
        return cls._convert_enum_value(
            v, ProcessingStatusEnum, ProcessingStatusEnum.NOT_DEFINE
        )

    def to_bitrix_dict(self) -> dict[str, Any]:
        # Преобразуем модель в словарь (с алиасами, без None)
        data = self.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,  # опционально: исключить неустановленные поля
        )

        # Дополнительные преобразования
        result: dict[str, Any] = {}
        for alias, value in data.items():
            if isinstance(value, bool):
                if alias in ("UF_CRM_60D2AFAEB32CC", "UF_CRM_1632738559"):
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

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class DealListResponse(BaseModel):  # type: ignore[misc]
    """Схема для ответа со списком сделок"""

    result: list[DealUpdate]
    next: int | None = None
    total: int

    #  model_config = ConfigDict(from_attributes=True)
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )
