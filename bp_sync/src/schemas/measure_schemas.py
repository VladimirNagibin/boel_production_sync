from pydantic import ConfigDict

from .base_schemas import CommonFieldMixin


class BaseMeasure(CommonFieldMixin):
    """
    Общие поля создания и обновления для соответствия SQLAlchemy модели
    """

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
        from_attributes=True,
    )


class MeasureCreate(BaseMeasure):
    measure_code: int
    name: str


class MeasureUpdate(BaseMeasure):
    measure_code: int | None
    name: str | None
