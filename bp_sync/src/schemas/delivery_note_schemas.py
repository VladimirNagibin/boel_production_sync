from pydantic import BaseModel, ConfigDict, Field

from .base_schemas import CommonFieldMixin, EntityAwareSchema
from .fields import FIELDS_DELIVERY


class BaseDeliveryNote(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE = FIELDS_DELIVERY

    company_id: int | None = Field(None)
    assigned_by_id: int | None = Field(None)
    invoice_id: int | None = Field(None)
    shipping_company_id: int | None = Field(None)
    warehouse_id: int | None = Field(None)

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class DeliveryNoteCreate(BaseDeliveryNote, EntityAwareSchema):
    """Модель для создания пользователей"""

    name: str = Field(...)
    opportunity: float = Field(0.0)


class DeliveryNoteUpdate(BaseDeliveryNote, BaseModel):  # type: ignore[misc]
    """Модель для частичного обновления пользователей"""

    name: str | None = Field(None)
    opportunity: float | None = Field(None)
