"""Роуты для управления заданиями на обработку счетов."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from schemas.invoice_task_schemas import InvoiceTaskCreate
from services.rabbitmq_client import RabbitMQClient, get_rabbitmq

from .deps import verify_api_key

invoice_tasks_router = APIRouter(dependencies=[Depends(verify_api_key)])


@invoice_tasks_router.post(
    "",
    summary="Добавить задание на обработку счёта",
    description=(
        "Добавляет задание в очередь обработки счетов. Повторное задание "
        "с тем же invoice_id и действием не создаётся."
    ),
)
async def add_invoice_task(
    task: InvoiceTaskCreate,
    rabbitmq_client: RabbitMQClient = Depends(get_rabbitmq),
) -> JSONResponse:
    """Добавляет задание на обработку счёта."""
    result, status_code = await rabbitmq_client.send_invoice_task(
        invoice_id=task.invoice_id,
        action=task.action,
    )
    return JSONResponse(
        status_code=int(status_code),
        content=result,
    )


@invoice_tasks_router.get(
    "",
    summary="Получить задание на обработку счёта",
    description="Получает одно задание из очереди обработки счетов.",
)
async def receive_invoice_task(
    rabbitmq_client: RabbitMQClient = Depends(get_rabbitmq),
) -> JSONResponse:
    """Получает одно задание из очереди без подтверждения."""
    message = await rabbitmq_client.get_invoice_task()
    if not message:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "No tasks available"},
        )

    try:
        body = json.loads(message.body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exp:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Некорректное тело сообщения: {exp}",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message_id": message.message_id,
            "invoice_id": body.get("invoice_id"),
            "action": body.get("action"),
            "instructions": (
                f"Call DELETE /api/v1/invoice-tasks/{message.message_id} "
                f"to mark task as processed, or POST "
                f"/api/v1/invoice-tasks/{message.message_id}/requeue "
                f"to return it to Ready"
            ),
        },
    )


@invoice_tasks_router.delete(
    "/{message_id}",
    summary="Удалить (подтвердить) задание",
    description=("Подтверждает обработку задания и удаляет его из очереди."),
)
async def delete_invoice_task(
    message_id: str,
    rabbitmq_client: RabbitMQClient = Depends(get_rabbitmq),
) -> JSONResponse:
    """Подтверждает обработку задания."""
    message = await rabbitmq_client.get_invoice_task_by_id(message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено или уже обработано",
        )

    success = await rabbitmq_client.ack_invoice_task_by_id(message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось подтвердить задание",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": f"Задание {message_id} обработано",
        },
    )


@invoice_tasks_router.post(
    "/{message_id}/requeue",
    summary="Вернуть задание из unacked в Ready",
    description=(
        "Возвращает полученное, но не подтверждённое задание обратно "
        "в очередь (Ready) для повторной обработки."
    ),
)
async def requeue_invoice_task(
    message_id: str,
    rabbitmq_client: RabbitMQClient = Depends(get_rabbitmq),
) -> JSONResponse:
    """Возвращает задание в Ready."""
    message = await rabbitmq_client.get_invoice_task_by_id(message_id)
    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задание не найдено или уже обработано",
        )

    success, status_text = await rabbitmq_client.requeue_invoice_task_by_id(
        message_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось вернуть задание в Ready",
        )

    if status_text == "discarded":
        message = (
            f"Задание {message_id} не возвращено в Ready: "
            f"дубль уже существует"
        )
    else:
        message = f"Задание {message_id} возвращено в Ready"

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": status_text,
            "message": message,
        },
    )
