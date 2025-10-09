import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from services.rabbitmq_client import RabbitMQClient, get_rabbitmq

from .deps import verify_api_key

messages_router = APIRouter(dependencies=[Depends(verify_api_key)])


@messages_router.get(
    "/receive_message",
    summary="Receive messages",
    description="Receive messages from RabbitMQ.",
)  # type: ignore
async def receive_message(
    rabbitmq_client: RabbitMQClient = Depends(get_rabbitmq),
) -> JSONResponse:
    message = await rabbitmq_client.get_message()
    if not message:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "No messages available"},
        )

    if message.message_id:
        async with rabbitmq_client._lock:
            rabbitmq_client.unacked_messages[message.message_id] = message
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message_id": message.message_id,
            "body": json.loads(message.body.decode()),
            "instructions": (
                f"Call /ack_message/{message.message_id} to confirm "
                "processing"
            ),
        },
    )


@messages_router.post(
    "/ack_message/{message_id}",
    summary="Acknowledge messages",
    description="Acknowledge messages in RabbitMQ.",
)  # type: ignore
async def acknowledge_message(
    message_id: str, rabbitmq_client: RabbitMQClient = Depends(get_rabbitmq)
) -> JSONResponse:
    async with rabbitmq_client._lock:
        if message_id not in rabbitmq_client.unacked_messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or already acknowledged",
            )

    message = rabbitmq_client.unacked_messages[message_id]
    success = await rabbitmq_client.ack_message(message)

    if success:
        del rabbitmq_client.unacked_messages[message_id]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Message {message_id} acknowledged",
            },
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge message",
        )
