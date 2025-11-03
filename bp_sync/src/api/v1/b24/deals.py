import time
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from core.settings import settings
from services.deals.deal_bitrix_services import DealBitrixClient
from services.deals.deal_import_services import DealProcessor
from services.deals.deal_services import DealClient
from services.deals.enums import NotificationScopeEnum
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

from ..deps import verify_api_key

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
    logger.info("Start loading deals")
    deal_ids: list[int] = (
        [int(deal_id)]
        if deal_id
        else await deal_bitrix_client.get_deal_ids_for_period(
            start_date, end_date
        )
    )
    logger.info(f"Loading deals total: {len(deal_ids)}")
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
        logger.info(f"Start loading deal id: {current_deal_id}")
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


@deals_router.get(
    "/status-deals",
    summary="Update deal processing statuses",
    description=(
        "Process and update deal processing statuses based on moved_date."
    ),
)  # type: ignore
async def status_deals(
    deal_client: DealClient = Depends(get_deal_client_dep),
    verify_api_key: str = Depends(verify_api_key),
) -> JSONResponse:
    """
    Endpoint для обновления статусов обработки сделок
    """
    logger.info("Start processing deal statuses")
    try:
        result = await deal_client.update_processing_statuses()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Deal processing completed successfully",
                "data": result,
                "timestamp": time.time(),
            },
        )

    except Exception as e:
        logger.error(f"Unhandled error in deal status processing: {e}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Deal processing failed",
                "error": str(e),
                "timestamp": time.time(),
            },
        )


@deals_router.get(
    "/notifications-overdue-deals",
    summary="Send overdue deals notifications",
    description=(
        "Sends notifications to managers or supervisors about overdue "
        "transactions."
        "If no parameters are specified, the default values are used."
    ),
    response_description="Result of notification sending",
)  # type: ignore
async def send_overdue_deals_notifications(
    notification_scope: int | None = Query(
        None,
        description="Notification scope: 0=All, 1=Supervisors, 2=Managers",
    ),
    chat_supervisor: int | None = Query(
        None, description="Supervisor chat ID (must be positive integer)"
    ),
    type_chat_supervisor: bool | None = Query(
        None, description="Type supervisor chat (True - chat, False - message)"
    ),
    deal_client: DealClient = Depends(get_deal_client_dep),
    verify_api_key: str = Depends(verify_api_key),
) -> JSONResponse:
    """
    Send notifications about overdue deals with parameter validation
    """
    try:
        # Валидация notification_scope
        if notification_scope is not None:
            try:
                validated_scope = NotificationScopeEnum(notification_scope)
                notification_scope = validated_scope
            except ValueError:
                valid_scopes = [scope.value for scope in NotificationScopeEnum]
                scope_names = [
                    f"{scope.value}={scope.name}"
                    for scope in NotificationScopeEnum
                ]

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Invalid notification_scope",
                        "valid_values": valid_scopes,
                        "valid_scopes_description": ", ".join(scope_names),
                        "received": notification_scope,
                    },
                )

        # Валидация chat_supervisor
        if chat_supervisor is not None and chat_supervisor <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chat_supervisor must be positive integer",
            )

        # Используем переданные значения или значения по умолчанию
        final_params: dict[str, Any] = {
            "notification_scope": (
                notification_scope or NotificationScopeEnum.SUPERVISOR
            ),
            "chat_supervisor": chat_supervisor or settings.CHAT_SUPERVISOR,
            "type_chat_supervisor": (
                type_chat_supervisor or settings.TYPE_CHAT_SUPERVISOR
            ),
        }
        await deal_client.send_notifications_overdue_deals(**final_params)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Notifications sent successfully",
                "used_parameters": final_params,
                "timestamp": time.time(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_overdue_deals_notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
