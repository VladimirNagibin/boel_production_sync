import time

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.bolashaq.products_service import (
    ProductHandler,
    get_products_service,
)

products_router = APIRouter(prefix="/products")


@products_router.post("/process")  # type: ignore
async def handle_bitrix24_webhook(
    request: Request,
    product_handler: ProductHandler = Depends(get_products_service),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для товаров

    - Принимает webhook в формате application/x-www-form-urlencoded
    - Валидирует подпись и данные
    - Обрабатывает поля
    - Записывает изменённые значения
    """
    logger.info("Received Bitrix24 webhook request product")
    try:
        return await product_handler.product_processing(request)
    except Exception as e:
        logger.error(f"Unhandled error in webhook handler: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "fail",
                "message": "Deal processing failed",
                "error": str(e),
                "timestamp": time.time(),
            },
        )


@products_router.post("/process_")  # type: ignore
async def handle_bitrix24_webhook_(
    product_id: int,
    product_handler: ProductHandler = Depends(get_products_service),
) -> bool:
    try:
        return await product_handler._transformation_fields(product_id)
    except Exception:  # as e:
        # logger.error(f"Unhandled error in webhook handler: {e}")
        return False
