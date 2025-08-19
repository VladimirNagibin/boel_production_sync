import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from core.logger import logger
from services.deals.deal_services import DealClient
from services.dependencies import get_deal_client_dep, request_context

EXCEL_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
reports_router = APIRouter(dependencies=[Depends(request_context)])


@reports_router.get("/export-deals/")  # type: ignore[misc]
async def export_deals(
    start_date: datetime = Query(
        ..., description="Дата начала в формате YYYY-MM-DD"
    ),
    end_date: datetime = Query(
        ..., description="Дата окончания в формате YYYY-MM-DD"
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    deal_client: DealClient = Depends(get_deal_client_dep),
) -> FileResponse:
    tmp_path = None
    try:
        tmp_path = await deal_client.export_deals_to_excel(
            start_date, end_date
        )

        background_tasks.add_task(cleanup_temp_file, tmp_path)

        return FileResponse(
            tmp_path,
            filename=(
                f"deals_export_{start_date.date()}_to_{end_date.date()}.xlsx"
            ),
            media_type=EXCEL_MEDIA_TYPE,
            background=background_tasks,
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Critical export error: {str(e)}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            cleanup_temp_file(tmp_path)
        raise HTTPException(
            status_code=500, detail="Internal server error during export"
        )


def cleanup_temp_file(path: str) -> None:
    """Удаляет временный файл с обработкой ошибок"""
    try:
        if os.path.exists(path):
            os.unlink(path)
            logger.info(f"Deleted temp file: {path}")
    except Exception as e:
        logger.error(f"Error deleting file {path}: {str(e)}")
