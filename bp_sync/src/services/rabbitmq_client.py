# import json
import uuid
from asyncio import Lock
from http import HTTPStatus
from typing import Any, Dict, Optional, Tuple

import aio_pika
from aio_pika import ExchangeType, Message
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
)
from aio_pika.exceptions import AMQPConnectionError, AMQPError

from core.logger import logger
from core.settings import settings

# from fastapi import FastAPI, HTTPException, Body


class RabbitMQClient:
    def __init__(self) -> None:
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None
        self.dlx_exchange: AbstractExchange | None = None
        self.queue: AbstractQueue | None = None
        self.dlq: AbstractQueue | None = None
        self.queue_name = "fastapi_queue"
        self._lock = Lock()  # Добавьте блокировку
        self.unacked_messages: Dict[str, AbstractIncomingMessage] = {}

    async def startup(self) -> None:
        """Инициализация подключения и объявление RabbitMQ объектов."""
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://{settings.RABBIT_USER}:{settings.RABBIT_PASSWORD}"
                f"@{settings.RABBIT_HOST}:{settings.RABBIT_PORT}/"
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)

            # Объявляем основной exchange
            self.exchange = await self.channel.declare_exchange(
                name=settings.EXCHANGE_NAME,
                type=ExchangeType.DIRECT,
                durable=True,
            )

            # Объявляем Dead Letter Exchange (DLX)
            self.dlx_exchange = await self.channel.declare_exchange(
                name="dlx_exchange",
                type=ExchangeType.FANOUT,
                durable=True,
            )

            # Объявляем Dead Letter Queue (DLQ)
            self.dlq = await self.channel.declare_queue(
                name="dead_letter_queue",
                durable=True,
            )
            await self.dlq.bind(self.dlx_exchange)

            # Объявляем основную очередь с DLX политикой
            self.queue = await self.channel.declare_queue(
                name=self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "dlx_exchange",
                    # "x-message-ttl": 130000,  # 130 секунд до dlx
                },
            )

            # Привязываем очередь к exchange
            await self.queue.bind(self.exchange, routing_key=self.queue_name)

            async with self._lock:
                self.unacked_messages.clear()

        except AMQPConnectionError as exp:
            logger.error(f"Ошибка подключения к RabbitMQ: {exp}")
            raise exp

    async def shutdown(self) -> None:
        """Корректное закрытие соединения."""
        if self.connection:
            try:
                await self.connection.close()
            except AMQPError as exp:
                logger.error(f"Ошибка при закрытии соединения: {exp}")

    async def ensure_connection(self) -> None:
        """Гарантирует наличие активного соединения."""
        if not self.connection or self.connection.is_closed:
            await self.startup()

    async def send_message(
        self, message_body: bytes
    ) -> Tuple[dict[str, Any], HTTPStatus]:
        """
        Отправка сообщения в RabbitMQ.

        :param message_body: Тело сообщения в bytes
        :return: Статус операции
        """
        try:
            await self.ensure_connection()

            if not self.exchange:
                raise RuntimeError("Exchange не инициализирован")

            message_id = str(uuid.uuid4())
            message = Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=message_id,
            )
            await self.exchange.publish(
                message=message,
                routing_key=self.queue_name,
            )

            logger.info(f"Отправлено сообщение: {message_id}")
            return {"message_id": message_id}, HTTPStatus.CREATED

        except Exception as exp:
            logger.error(f"Ошибка при отправке сообщения: {exp}")
            return {"error": str(exp)}, HTTPStatus.BAD_REQUEST

    async def get_message(
        self,
    ) -> Optional[aio_pika.abc.AbstractIncomingMessage]:
        """Получение одного сообщения из очереди без подтверждения"""
        try:
            await self.ensure_connection()

            if not self.queue:
                raise RuntimeError("Очередь не инициализирована")

            return await self.queue.get(fail=False, no_ack=False)
        except Exception as exp:
            logger.error(f"Ошибка при получении сообщения: {exp}")
            return None

    async def ack_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> bool:
        """Подтверждение успешной обработки сообщения"""
        try:
            await message.ack()
            return True
        except Exception as exp:
            logger.error(f"Ошибка при подтверждении сообщения: {exp}")
            return False


_rabbitmq_instance = None


def get_rabbitmq() -> RabbitMQClient:
    global _rabbitmq_instance
    if _rabbitmq_instance is None:
        _rabbitmq_instance = RabbitMQClient()
    return _rabbitmq_instance
