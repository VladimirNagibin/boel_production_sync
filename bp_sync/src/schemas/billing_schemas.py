from datetime import date
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.enums import MethodPaymentEnum

from .base_schemas import BitrixValidators, CommonFieldMixin, EntityAwareSchema
from .fields import FIELDS_BILLING


class BaseBilling(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_BILLING

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class BillingCreate(BaseBilling, EntityAwareSchema):
    """Модель для создания пользователей"""

    payment_method: MethodPaymentEnum = Field(MethodPaymentEnum.NOT_DEFINE)

    name: str = Field(...)
    amount: float = Field(0.0)
    date_payment: date = Field(...)
    number: str = Field(...)
    delivery_note_id: str = Field(...)

    @field_validator("payment_method", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_method(cls, v: Any) -> MethodPaymentEnum:
        return BitrixValidators.convert_enum(
            v, MethodPaymentEnum, MethodPaymentEnum.NOT_DEFINE
        )


class BillingUpdate(BaseBilling, BaseModel):  # type: ignore[misc]
    """Модель для частичного обновления пользователей"""

    payment_method: MethodPaymentEnum | None = Field(None)

    name: str | None = Field(None)
    amount: float | None = Field(None)
    date_payment: date | None = Field(None)
    number: str | None = Field(None)
    delivery_note_id: str | None = Field(None)

    @field_validator("payment_method", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_payment_method(cls, v: Any) -> MethodPaymentEnum:
        return BitrixValidators.convert_enum(
            v, MethodPaymentEnum, MethodPaymentEnum.NOT_DEFINE
        )
