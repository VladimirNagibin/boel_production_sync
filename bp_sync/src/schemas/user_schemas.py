from datetime import datetime
from typing import ClassVar

from pydantic import ConfigDict, Field, field_validator

from .base_schemas import CommonFieldMixin, EntityAwareSchema
from .fields import FIELDS_USER


class BaseUser(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_USER

    # Идентификаторы и основные данные
    name: str | None = Field(None, alias="NAME")
    second_name: str | None = Field(None, alias="SECOND_NAME")
    last_name: str | None = Field(None, alias="LAST_NAME")
    xml_id: str | None = Field(None, alias="XML_ID")
    personal_gender: str | None = Field(None, alias="PERSONAL_GENDER")
    work_position: str | None = Field(None, alias="WORK_POSITION")
    user_type: str | None = Field(None, alias="USER_TYPE")

    # Временные метки
    last_login: datetime | None = Field(None, alias="LAST_LOGIN")
    date_register: datetime | None = Field(None, alias="DATE_REGISTER")
    personal_birthday: datetime | None = Field(None, alias="PERSONAL_BIRTHDAY")
    employment_date: datetime | None = Field(None, alias="UF_EMPLOYMENT_DATE")
    date_new: datetime | None = Field(None, alias="UF_USR_1699347879988")

    # География и источники
    time_zone: str | None = Field(None, alias="TIME_ZONE")
    personal_city: str | None = Field(None, alias="PERSONAL_CITY")

    # Коммуникации
    email: str | None = Field(None, alias="EMAIL")
    personal_mobile: str | None = Field(None, alias="PERSONAL_MOBILE")
    work_phone: str | None = Field(None, alias="WORK_PHONE")
    personal_www: str | None = Field(None, alias="PERSONAL_WWW")

    # Связи с другими сущностями
    department_id: int | None = Field(None, alias="UF_DEPARTMENT")

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class UserCreate(BaseUser, EntityAwareSchema):
    """Модель для создания пользователей"""

    # external_id: int = Field(..., alias="ID")

    # Статусы и флаги
    active: bool = Field(False, alias="ACTIVE")
    is_online: bool = Field(False, alias="IS_ONLINE")


class UserUpdate(BaseUser):
    """Модель для частичного обновления пользователей"""

    # external_id: int | None = Field(None, alias="ID")

    # Статусы и флаги
    active: bool | None = Field(None, alias="ACTIVE")
    is_online: bool | None = Field(None, alias="IS_ONLINE")
