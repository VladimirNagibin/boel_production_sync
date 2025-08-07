from typing import Any

from pydantic import ConfigDict, Field

from .base_schemas import CommonFieldMixin


class Department(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    name: str = Field(alias="NAME")
    parent_id: int | None = Field(None, alias="PARENT")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    def model_dump_db(self, exclude_unset: bool = False) -> dict[str, Any]:
        return self.model_dump(  # type: ignore[no-any-return]
            exclude_unset=exclude_unset
        )
