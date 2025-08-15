from schemas.timeline_comment_schemas import (
    TimelineCommentCreate,
    TimelineCommentUpdate,
)

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient


class TimeLineCommentBitrixClient(
    BaseBitrixEntityClient[TimelineCommentCreate, TimelineCommentUpdate]
):
    entity_name = "timeline.comment"
    create_schema = TimelineCommentCreate
    update_schema = TimelineCommentUpdate
