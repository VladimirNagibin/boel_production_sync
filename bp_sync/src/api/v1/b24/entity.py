import time

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.base_services.base_service import BaseEntityClient
from services.companies.company_services import CompanyClient
from services.dependencies import (
    get_company_client_dep,
)

entity_router = APIRouter(prefix="/entities")


@entity_router.post("/handle-webhook/company")  # type: ignore
async def handle_bitrix24_webhook_company(
    request: Request,
    company_client: CompanyClient = Depends(get_company_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для компаний
    """
    return await _handle_bitrix24_webhook(request, company_client)


async def _handle_bitrix24_webhook(
    request: Request,
    entity_client: BaseEntityClient,  # type: ignore[type-arg]
    entity_type_id: int | None = None,
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для сделок

    - Принимает webhook в формате application/x-www-form-urlencoded
    - Валидирует подпись и данные
    - Обрабатывает тестовые и продакшен сделки
    - Возвращает детализированные ответы
    """
    logger.info("Received Bitrix24 webhook request")
    try:
        return await entity_client.entity_processing(request, entity_type_id)
    except Exception as e:
        logger.error(f"Unhandled error in webhook handler: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "fail",
                "message": "Entity processing failed",
                "error": str(e),
                "timestamp": time.time(),
            },
        )
