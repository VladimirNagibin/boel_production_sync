from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from core.logger import logger
from core.settings import settings
from schemas.deal_schemas import BitrixWebhookAuth, BitrixWebhookPayload

# from services.bitrix_services.webhook_service import verify_webhook
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


@deals_router.post(
    "/process_",
    summary="Handling deal",
    description="Processing deal.",
)  # type: ignore
async def handle_bitrix24_webhook(  # type: ignore
    request: Request,
    payload: BitrixWebhookPayload,  # = Depends(verify_webhook),
    deal_client: DealClient = Depends(get_deal_client_dep),
):
    """
    Обработчик вебхуков от Bitrix24
    """
    try:
        # Логируем получение вебхука
        print(
            f"Получен вебхук: {payload.event} для обработчика "
            f"{payload.event_handler_id}"
        )

        # Обработка в зависимости от типа события
        if payload.event == "ONCRMDEALUPDATE":
            deal_id = int(payload.data.get("FIELDS", {}).get("ID"))
            if deal_id and deal_id == 54195:  # TEST ++++++++++++++++++++
                await deal_client.bitrix_client.send_message_b24(
                    171, "NEW PROCESS"
                )
                success = await deal_client.handle_deal(deal_id)

                if success:
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "status": "success",
                            "message": f"Deal {deal_id} processed success",
                            "event": payload.event,
                        },
                    )
                else:
                    return JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={
                            "status": "error",
                            "message": f"Failed to process deal {deal_id}",
                            "event": payload.event,
                        },
                    )
            else:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "status": "error",
                        "message": "Deal ID not found in webhook data",
                        "event": payload.event,
                    },
                )

        # Добавьте обработку других событий по необходимости
        elif payload.event == "ONCRMDEALADD":
            # Обработка создания сделки
            pass
        elif payload.event == "ONCRMDEALDELETE":
            # Обработка удаления сделки
            pass

        # Для неподдерживаемых событий возвращаем успех, но логируем
        print(f"Unhandled event type: {payload.event}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Webhook received but no specific handler",
                "event": payload.event,
            },
        )

    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Альтернативная версия с raw JSON обработкой
@deals_router.post("/process")  # type: ignore
async def handle_bitrix24_webhook_raw(
    request: Request,
    deal_client: DealClient = Depends(get_deal_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхуков с прямой обработкой JSON
    """
    await deal_client.bitrix_client.send_message_b24(171, "NEW PROCESS DEAL")

    try:
        webhook_payload: BitrixWebhookPayload | None = await process_webhook(
            request
        )
        if not webhook_payload:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": "Failed to process deal",
                    "event": "Not define",
                },
            )
        await deal_client.bitrix_client.send_message_b24(
            171, str(webhook_payload.model_dump_json())
        )

        # Проверка токена
        auth = webhook_payload.auth
        expected_domain = settings.web_hook_config["expected_tokens"].get(
            auth.application_token
        )
        if expected_domain != auth.domain:
            raise HTTPException(
                status_code=401, detail="Invalid webhook token"
            )

        # Обработка события
        event = webhook_payload.event
        deal_id = webhook_payload.data["FIELDS"]["ID"]
        await deal_client.bitrix_client.send_message_b24(
            171, f"{deal_id}:: DEAL_ID"
        )
        if event == "ONCRMDEALUPDATE" and deal_id and deal_id == 54195:  # TEST
            await deal_client.bitrix_client.send_message_b24(
                171, "NEW PROCESS"
            )
            success = await deal_client.handle_deal(deal_id)

            if success:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "status": "success",
                        "message": f"Deal {deal_id} processed success",
                        "event": webhook_payload.event,
                    },
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "status": "error",
                        "message": f"Failed to process deal {deal_id}",
                        "event": webhook_payload.event,
                    },
                )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Webhook received but no specific handler",
                "event": webhook_payload.event,
            },
        )

    except Exception as e:
        print(f"Error in raw webhook handler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def process_webhook(request: Request) -> BitrixWebhookPayload | None:
    form_data = await request.form()
    parsed_body = dict(form_data)

    # Преобразуем плоскую структуру во вложенную
    structured_data: dict[str, Any] = {}

    for key, value in parsed_body.items():
        # Обрабатываем вложенные ключи вида data[FIELDS][ID]
        if "[" in key and "]" in key:
            parts = key.replace("]", "").split("[")
            current_level = structured_data

            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current_level[part] = value
                else:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]
        else:
            structured_data[key] = value

    # Создаем объект BitrixWebhookPayload
    try:
        webhook_payload = BitrixWebhookPayload(
            event=structured_data.get("event", ""),
            event_handler_id=structured_data.get("event_handler_id", ""),
            data=structured_data.get("data", {}),
            ts=structured_data.get("ts", ""),
            auth=BitrixWebhookAuth(
                domain=structured_data.get("auth", {}).get("domain", ""),
                client_endpoint=structured_data.get("auth", {}).get(
                    "client_endpoint", ""
                ),
                server_endpoint=structured_data.get("auth", {}).get(
                    "server_endpoint", ""
                ),
                member_id=structured_data.get("auth", {}).get("member_id", ""),
                application_token=structured_data.get("auth", {}).get(
                    "application_token", ""
                ),
            ),
        )

        print(
            f"Обработан вебхук: {webhook_payload.event} для сделки "
            f"{webhook_payload.data.get('FIELDS', {}).get('ID')}"
        )
        return webhook_payload

    except ValidationError as e:
        print(f"Ошибка валидации: {e}")
        return None
