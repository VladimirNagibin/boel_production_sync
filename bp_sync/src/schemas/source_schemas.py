from typing import Any

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):  # type: ignore[misc]
    """
    Общие поля создания и обновления для соответствия SQLAlchemy модели
    """

    external_id: str
    name: str

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
