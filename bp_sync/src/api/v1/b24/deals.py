import time
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.deals.deal_bitrix_services import DealBitrixClient
from services.deals.deal_import_services import DealProcessor
from services.deals.deal_services import DealClient
from services.dependencies import (
    get_deal_bitrix_client_dep,
    get_deal_client_dep,
    get_invoice_bitrix_client_dep,
    get_invoice_client_dep,
    get_timeline_comment_bitrix_client_dep,
    get_timeline_comment_repository_dep,
)
from services.invoices.invoice_bitrix_services import InvoiceBitrixClient
from services.invoices.invoice_services import InvoiceClient
from services.rabbitmq_client import RabbitMQClient, get_rabbitmq
from services.timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from services.timeline_comments.timeline_comment_repository import (
    TimelineCommentRepository,
)

deals_router = APIRouter(prefix="/deals")


@deals_router.get(
    "/load-deals",
    summary="Load deals",
    description="Uploading deals for period to db.",
)  # type: ignore
async def load_deals(
    start_date: date = Query(
        ..., description="Дата начала в формате YYYY-MM-DD"
    ),
    end_date: date = Query(
        ..., description="Дата окончания в формате YYYY-MM-DD"
    ),
    deal_id: int | str | None = None,
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client_dep),
    deal_client: DealClient = Depends(get_deal_client_dep),
    invoice_bitrix_client: InvoiceBitrixClient = Depends(
        get_invoice_bitrix_client_dep
    ),
    invoice_client: InvoiceClient = Depends(get_invoice_client_dep),
    rabbitmq_client: RabbitMQClient = Depends(get_rabbitmq),
    timeline_client: TimeLineCommentBitrixClient = Depends(
        get_timeline_comment_bitrix_client_dep
    ),
    timeline_repo: TimelineCommentRepository = Depends(
        get_timeline_comment_repository_dep
    ),
) -> JSONResponse:

    deal_ids: list[int] = (
        [int(deal_id)]
        if deal_id
        else await deal_bitrix_client.get_deal_ids_for_period(
            start_date, end_date
        )
    )

    # Инициализируем процессор
    processor = DealProcessor(
        deal_client=deal_client,
        invoice_bitrix_client=invoice_bitrix_client,
        invoice_client=invoice_client,
        timeline_client=timeline_client,
        timeline_repo=timeline_repo,
        rabbitmq_client=rabbitmq_client,
    )

    # Обрабатываем сделки
    deal_success: dict[str, Any] = {}
    deal_fail: dict[str, Any] = {}

    for current_deal_id in deal_ids:
        if not current_deal_id:
            continue

        is_success, message = await processor.process_single_deal(
            int(current_deal_id)
        )

        if is_success:
            deal_success[str(current_deal_id)] = message
        else:
            deal_fail[str(current_deal_id)] = message

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "deal_success": deal_success,
            "deal_fail": deal_fail,
            "total_processed": len(deal_ids),
            "successful": len(deal_success),
            "failed": len(deal_fail),
        },
    )


@deals_router.post(
    "/set-source",
    summary="Set source deal",
    description="Updating and fixing source deal.",
)  # type: ignore
async def set_deal_source(
    user_id: str = Query(..., description="ID пользователя из шаблона"),
    key: str = Query(..., description="Секретный ключ из глобальных констант"),
    deal_id: str = Query(..., description="ID сделки"),
    creation_source: str | None = Query(None, description="Источник создания"),
    source: str | None = Query(None, description="Источник"),
    type_deal: str | None = Query(
        None, alias="type", description="Тип источника"
    ),
    deal_client: DealClient = Depends(get_deal_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхука из Битрикс24 для установки источника сделки.

    URL: http://portal:8000/api/v1/b24/set-source
    Параметры:
      - user_id={=Template:TargetUser}
      - key={{Константы глобальные: ключ}}
      - deal_id={{ID}}
      - creation_source={=Template:CreationSource}
      - source={=Template:Source}
      - type={=Template:Type}
    """

    try:
        success = await deal_client.set_deal_source(
            user_id, key, deal_id, creation_source, source, type_deal
        )

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Deal source updated successfully",
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": "Failed to update deal source",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in set_source_deal: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Internal server error"},
        )


@deals_router.post("/process")  # type: ignore
async def handle_bitrix24_webhook_raw(
    request: Request,
    deal_client: DealClient = Depends(get_deal_client_dep),
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
        return await deal_client.deal_processing(request)
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
