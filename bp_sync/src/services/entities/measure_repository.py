from models.references import Measure as MeasureDB
from schemas.measure_schemas import MeasureCreate, MeasureUpdate

from ..base_repositories.base_repository import BaseRepository


class MeasureRepository(
    BaseRepository[MeasureDB, MeasureCreate, MeasureUpdate, int]
):

    model = MeasureDB

    async def get_entity(self, external_id: int) -> MeasureCreate | None:
        measure_db = await self.get(external_id)
        if measure_db:
            return MeasureCreate(
                internal_id=measure_db.id,
                created_at=measure_db.created_at,
                updated_at=measure_db.updated_at,
                is_deleted_in_bitrix=measure_db.is_deleted_in_bitrix,
                id=measure_db.external_id,
                name=measure_db.name,
                measure_code=measure_db.measure_code,
            )
        return None
