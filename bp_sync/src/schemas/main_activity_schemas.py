from pydantic import ConfigDict

from models.bases import EntityType

from .base_schemas import CommonFieldMixin


class BaseMainActivity(CommonFieldMixin):
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


class MainActivityCreate(BaseMainActivity):
    name: str
    ext_alt_id: int
    ext_alt2_id: int
    ext_alt3_id: int
    ext_alt4_id: int

    def get_id_entity(self, entity: EntityType) -> int | None:
        if entity == EntityType.DEAL:
            if self.external_id:
                return int(self.external_id)
        if entity == EntityType.LEAD:
            return self.ext_alt_id
        if entity == EntityType.CONTACT:
            return self.ext_alt2_id
        if entity == EntityType.COMPANY:
            return self.ext_alt3_id
        if entity == EntityType.INVOICE:
            return self.ext_alt4_id
        return None


class MainActivityUpdate(BaseMainActivity):
    name: str | None
    ext_alt_id: int | None
    ext_alt2_id: int | None
    ext_alt3_id: int | None
    ext_alt4_id: int | None
