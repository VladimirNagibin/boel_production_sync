from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseCreateSchema(BaseModel):  # type: ignore[misc]
    """Базовая схема для создания сущностей"""

    external_id: int = Field(..., alias="ID")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class BaseUpdateSchema(BaseModel):  # type: ignore[misc]
    """Базовая схема для обновления сущностей"""

    external_id: Optional[int] = Field(None, alias="ID")

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
