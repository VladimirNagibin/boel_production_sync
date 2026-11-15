"""Роуты для выдачи очередных номеров документов."""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from models.numbering import DocumentType
from services.dependencies import (
    get_numbering_service_dep,
    request_context,
)
from services.numbering.numbering_service import NumberingService

from .deps import verify_api_key

numbering_router = APIRouter(
    dependencies=[Depends(request_context), Depends(verify_api_key)]
)


@numbering_router.get(  # type: ignore[misc]
    "/number",
    summary="Получить очередной номер документа",
)
async def get_document_number(
    id_firm: int = Query(..., description="ID фирмы отгрузки"),
    doc_type: DocumentType = Query(..., description="Тип документа"),
    numbering_service: NumberingService = Depends(get_numbering_service_dep),
) -> JSONResponse:
    """Возвращает отформатированный очередной номер документа."""
    result = await numbering_service.get_next_number(id_firm, doc_type)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "number": result.number,
            "id_firm": id_firm,
            "doc_type": doc_type.value,
            "current_number": result.current_number,
        },
    )
