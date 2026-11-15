"""Клиент для взаимодействия с RabbitMQ.

Содержит методы для работы с основной очередью синхронизации и
отдельной очередью заданий на обработку счетов.
"""

import asyncio
import json
import uuid
from asyncio import Lock
from http import HTTPStatus
from typing import Any, Awaitable, Callable, Optional, TypeVar

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
from schemas.invoice_task_schemas import InvoiceTaskAction

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 0.5

INVOICE_TASK_QUEUE_NAME = "invoice_task_queue"
INVOICE_TASK_EXCHANGE_NAME = "invoice_task_exchange"
INVOICE_TASK_DLX_EXCHANGE_NAME = "invoice_task_dlx_exchange"
INVOICE_TASK_DLQ_NAME = "invoice_task_dead_letter_queue"

_T = TypeVar("_T")


class RabbitMQClient:
    """Клиент RabbitMQ для публикации и получения сообщений."""

    def __init__(self) -> None:
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None
        self.dlx_exchange: AbstractExchange | None = None
        self.queue: AbstractQueue | None = None
        self.dlq: AbstractQueue | None = None
        self.queue_name = "fastapi_queue"
        self._lock = Lock()
        self.unacked_messages: dict[str, AbstractIncomingMessage] = {}

        self.invoice_task_exchange: AbstractExchange | None = None
        self.invoice_task_dlx_exchange: AbstractExchange | None = None
        self.invoice_task_queue: AbstractQueue | None = None
        self.invoice_task_dlq: AbstractQueue | None = None
        self._pending_invoice_tasks: set[str] = set()
        self._unacked_invoice_tasks: dict[str, AbstractIncomingMessage] = {}
        self._invoice_task_original_keys: dict[str, str] = {}

    async def startup(self) -> None:
        """Инициализация подключения и объявление объектов RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://{settings.RABBIT_USER}:"
                f"{settings.RABBIT_PASSWORD}@"
                f"{settings.RABBIT_HOST}:{settings.RABBIT_PORT}/"
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)

            self.exchange = await self.channel.declare_exchange(
                name=settings.EXCHANGE_NAME,
                type=ExchangeType.DIRECT,
                durable=True,
            )

            self.dlx_exchange = await self.channel.declare_exchange(
                name="dlx_exchange",
                type=ExchangeType.FANOUT,
                durable=True,
            )

            self.dlq = await self.channel.declare_queue(
                name="dead_letter_queue",
                durable=True,
            )
            await self.dlq.bind(self.dlx_exchange)

            self.queue = await self.channel.declare_queue(
                name=self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "dlx_exchange",
                },
            )
            await self.queue.bind(self.exchange, routing_key=self.queue_name)

            await self._declare_invoice_task_topology()

            async with self._lock:
                self.unacked_messages.clear()
                self._unacked_invoice_tasks.clear()
                self._invoice_task_original_keys.clear()

        except AMQPConnectionError as exp:
            logger.error("Ошибка подключения к RabbitMQ: %s", exp)
            raise

    async def _declare_invoice_task_topology(self) -> None:
        """Объявляет очередь и exchange для заданий по счетам."""
        if not self.channel:
            raise RuntimeError("Канал RabbitMQ не инициализирован")

        self.invoice_task_dlx_exchange = await self.channel.declare_exchange(
            name=INVOICE_TASK_DLX_EXCHANGE_NAME,
            type=ExchangeType.FANOUT,
            durable=True,
        )
        self.invoice_task_dlq = await self.channel.declare_queue(
            name=INVOICE_TASK_DLQ_NAME,
            durable=True,
        )
        await self.invoice_task_dlq.bind(self.invoice_task_dlx_exchange)

        self.invoice_task_exchange = await self.channel.declare_exchange(
            name=INVOICE_TASK_EXCHANGE_NAME,
            type=ExchangeType.DIRECT,
            durable=True,
        )
        self.invoice_task_queue = await self.channel.declare_queue(
            name=INVOICE_TASK_QUEUE_NAME,
            durable=True,
            arguments={
                "x-dead-letter-exchange": INVOICE_TASK_DLX_EXCHANGE_NAME,
            },
        )
        await self.invoice_task_queue.bind(
            self.invoice_task_exchange,
            routing_key=INVOICE_TASK_QUEUE_NAME,
        )

    async def shutdown(self) -> None:
        """Корректное закрытие соединения."""
        if self.connection:
            try:
                await self.connection.close()
            except AMQPError as exp:
                logger.error("Ошибка при закрытии соединения: %s", exp)

    async def ensure_connection(self) -> None:
        """Гарантирует наличие активного соединения."""
        if not self.connection or self.connection.is_closed:
            await self.startup()

    async def _run_with_retry(
        self,
        operation: Callable[..., Awaitable[_T]],
        *args: Any,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_RETRY_BASE_DELAY,
        **kwargs: Any,
    ) -> _T:
        """Выполняет операцию RabbitMQ с повторными попытками.

        Повторы выполняются только для временных ошибок RabbitMQ и
        сетевых ошибок.
        """
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except (AMQPConnectionError, AMQPError, OSError) as exp:
                last_error = exp
                if attempt >= max_retries:
                    logger.error(
                        "Операция RabbitMQ не удалась после %s попыток: %s",
                        max_retries + 1,
                        exp,
                    )
                    break

                delay = base_delay * (2**attempt)
                logger.warning(
                    "Ошибка RabbitMQ: %s. "
                    "Повторная попытка %s из %s через %.2fс",
                    exp,
                    attempt + 1,
                    max_retries,
                    delay,
                )
                await asyncio.sleep(delay)

        assert last_error is not None
        raise last_error

    async def _ensure_connection_with_retry(self) -> None:
        """Гарантирует активное соединение с повторными попытками."""
        if not self.connection or self.connection.is_closed:
            await self._run_with_retry(self.startup)

    async def send_message(
        self, message_body: bytes
    ) -> tuple[dict[str, Any], HTTPStatus]:
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

            logger.info("Отправлено сообщение: %s", message_id)
            return {"message_id": message_id}, HTTPStatus.CREATED

        except Exception as exp:
            logger.error("Ошибка при отправке сообщения: %s", exp)
            return {"error": str(exp)}, HTTPStatus.BAD_REQUEST

    async def get_message(
        self,
    ) -> Optional[AbstractIncomingMessage]:
        """Получение одного сообщения из очереди без подтверждения."""
        try:
            await self.ensure_connection()

            if not self.queue:
                raise RuntimeError("Очередь не инициализирована")

            return await self.queue.get(fail=False, no_ack=False)
        except Exception as exp:
            logger.error("Ошибка при получении сообщения: %s", exp)
            return None

    async def ack_message(self, message: AbstractIncomingMessage) -> bool:
        """Подтверждение успешной обработки сообщения."""
        try:
            await message.ack()
            return True
        except Exception as exp:
            logger.error("Ошибка при подтверждении сообщения: %s", exp)
            return False

    @staticmethod
    def _build_invoice_task_key(
        invoice_id: int, action: InvoiceTaskAction
    ) -> str:
        """Формирует детерминированный ключ задания для дедупликации."""
        return f"invoice_task:{invoice_id}:{action.value}"

    async def send_invoice_task(
        self,
        invoice_id: int,
        action: InvoiceTaskAction,
    ) -> tuple[dict[str, Any], HTTPStatus]:
        """Добавляет задание на обработку счёта в отдельную очередь.

        Если задание с таким же ``invoice_id`` и ``action`` уже ожидает
        обработки, повторно оно не добавляется.

        :param invoice_id: Идентификатор счёта.
        :param action: Действие, которое необходимо выполнить.
        :return: Словарь с результатом и HTTP-статус операции.
        """
        if invoice_id <= 0:
            return (
                {"error": "invoice_id должен быть положительным числом"},
                HTTPStatus.BAD_REQUEST,
            )

        task_key = self._build_invoice_task_key(invoice_id, action)

        try:
            await self._ensure_connection_with_retry()

            if not self.invoice_task_exchange:
                raise RuntimeError(
                    "Exchange для заданий по счетам не инициализирован"
                )

            async with self._lock:
                if task_key in self._pending_invoice_tasks:
                    logger.info("Задание %s уже находится в очереди", task_key)
                    return (
                        {
                            "message_id": task_key,
                            "invoice_id": invoice_id,
                            "action": action.value,
                            "status": "already_queued",
                        },
                        HTTPStatus.CONFLICT,
                    )
                self._pending_invoice_tasks.add(task_key)

            try:
                body = json.dumps(
                    {
                        "invoice_id": invoice_id,
                        "action": action.value,
                    },
                    ensure_ascii=False,
                ).encode("utf-8")

                message = Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=task_key,
                    content_type="application/json",
                    headers={
                        "invoice_id": invoice_id,
                        "action": action.value,
                    },
                )
                await self._run_with_retry(
                    self.invoice_task_exchange.publish,
                    message=message,
                    routing_key=INVOICE_TASK_QUEUE_NAME,
                )
            except Exception:
                async with self._lock:
                    self._pending_invoice_tasks.discard(task_key)
                raise

        except Exception as exp:
            logger.error("Ошибка при добавлении задания: %s", exp)
            return {"error": str(exp)}, HTTPStatus.SERVICE_UNAVAILABLE

        logger.info("Добавлено задание на обработку счёта: %s", task_key)
        return (
            {
                "message_id": task_key,
                "invoice_id": invoice_id,
                "action": action.value,
                "status": "queued",
            },
            HTTPStatus.CREATED,
        )

    async def get_invoice_task(
        self,
    ) -> Optional[AbstractIncomingMessage]:
        """Получает одно задание из очереди без подтверждения.

        После получения заданию присваивается уникальный ключ обработки,
        а исходный ключ дедупликации освобождается, чтобы можно было
        добавить повторное задание с тем же invoice_id и действием.
        """
        try:
            await self._ensure_connection_with_retry()

            if not self.invoice_task_queue:
                raise RuntimeError(
                    "Очередь заданий по счетам не инициализирована"
                )

            message = await self._run_with_retry(
                self.invoice_task_queue.get,
                fail=False,
                no_ack=False,
            )
        except Exception as exp:
            logger.error("Ошибка при получении задания: %s", exp)
            return None

        if message and message.message_id:
            original_key = message.message_id
            message.message_id = str(uuid.uuid4())

            async with self._lock:
                self._pending_invoice_tasks.discard(original_key)
                self._unacked_invoice_tasks[message.message_id] = message
                self._invoice_task_original_keys[message.message_id] = (
                    original_key
                )

            logger.info(
                "Задание %s получено, присвоен ключ обработки %s",
                original_key,
                message.message_id,
            )

        return message

    async def get_invoice_task_by_id(
        self, message_id: str
    ) -> Optional[AbstractIncomingMessage]:
        """Возвращает необработанное задание по идентификатору."""
        async with self._lock:
            return self._unacked_invoice_tasks.get(message_id)

    async def ack_invoice_task(self, message: AbstractIncomingMessage) -> bool:
        """Подтверждает обработку задания (перенос в обработанные)."""
        try:
            await self._run_with_retry(message.ack)
        except Exception as exp:
            logger.error("Ошибка при подтверждении задания: %s", exp)
            return False

        receipt_id = message.message_id
        async with self._lock:
            if receipt_id:
                self._unacked_invoice_tasks.pop(receipt_id, None)
                self._invoice_task_original_keys.pop(receipt_id, None)
        return True

    async def ack_invoice_task_by_id(self, message_id: str) -> bool:
        """Подтверждает задание по его идентификатору."""
        message = await self.get_invoice_task_by_id(message_id)
        if message is None:
            logger.warning(
                "Задание %s не найдено среди необработанных", message_id
            )
            return False
        return await self.ack_invoice_task(message)

    async def reject_invoice_task(
        self,
        message: AbstractIncomingMessage,
        requeue: bool = True,
    ) -> bool:
        """Отклоняет задание.

        При ``requeue=True`` возврат в Ready выполняется с проверкой
        дедупликации; при ``requeue=False`` сообщение отбрасывается.
        """
        if requeue:
            success, _ = await self.requeue_invoice_task(message)
            return success

        try:
            await self._run_with_retry(message.reject, requeue=False)
        except Exception as exp:
            logger.error("Ошибка при отклонении задания: %s", exp)
            return False

        receipt_id = message.message_id
        async with self._lock:
            if receipt_id:
                self._invoice_task_original_keys.pop(receipt_id, None)
                self._unacked_invoice_tasks.pop(receipt_id, None)
        return True

    async def requeue_invoice_task(
        self, message: AbstractIncomingMessage
    ) -> tuple[bool, str]:
        """Возвращает задание из unacked обратно в Ready с проверкой дублей.

        Если по исходному ключу задания уже есть дубль в очереди, текущее
        сообщение подтверждается и не возвращается в Ready.

        :return: Кортеж ``(успех, статус)``, где статус может быть
            ``requeued`` или ``discarded``.
        """
        receipt_id = message.message_id

        async with self._lock:
            original_key = self._invoice_task_original_keys.get(receipt_id)
            has_duplicate = bool(
                original_key and original_key in self._pending_invoice_tasks
            )
            if not has_duplicate and original_key:
                self._pending_invoice_tasks.add(original_key)

        if has_duplicate:
            try:
                await self._run_with_retry(message.ack)
            except Exception as exp:
                logger.error("Ошибка при подтверждении дубля: %s", exp)
                return False, "error"

            async with self._lock:
                self._unacked_invoice_tasks.pop(receipt_id, None)
                self._invoice_task_original_keys.pop(receipt_id, None)

            logger.info(
                "Задание %s не возвращено в Ready: дубль уже существует",
                original_key,
            )
            return True, "discarded"

        try:
            await self._run_with_retry(message.reject, requeue=True)
        except Exception as exp:
            logger.error("Ошибка при возврате задания в Ready: %s", exp)
            async with self._lock:
                if original_key:
                    self._pending_invoice_tasks.discard(original_key)
            return False, "error"

        async with self._lock:
            if receipt_id:
                self._unacked_invoice_tasks.pop(receipt_id, None)
                self._invoice_task_original_keys.pop(receipt_id, None)

        return True, "requeued"

    async def requeue_invoice_task_by_id(
        self, message_id: str
    ) -> tuple[bool, str]:
        """Возвращает задание по идентификатору из unacked в Ready."""
        message = await self.get_invoice_task_by_id(message_id)
        if message is None:
            logger.warning(
                "Задание %s не найдено среди необработанных", message_id
            )
            return False, "error"
        return await self.requeue_invoice_task(message)


_rabbitmq_instance: RabbitMQClient | None = None


def get_rabbitmq() -> RabbitMQClient:
    """Возвращает singleton-экземпляр клиента RabbitMQ."""
    global _rabbitmq_instance
    if _rabbitmq_instance is None:
        _rabbitmq_instance = RabbitMQClient()
    return _rabbitmq_instance
