import time
from typing import Any
from urllib.parse import unquote

from fastapi import Request
from pydantic import ValidationError

from core.logger import logger
from core.settings import settings
from schemas.deal_schemas import BitrixWebhookAuth, BitrixWebhookPayload

from ..exceptions import WebhookSecurityError, WebhookValidationError


class WebhookService:
    """Сервис для обработки и валидации вебхуков Bitrix24"""

    MAX_AGE = 300

    def __init__(
        self,
        allowed_events: set[Any] = set(
            settings.web_hook_config.get("allowed_events", [])
        ),
        expected_tokens: dict[str, Any] = settings.web_hook_config.get(
            "expected_tokens", {}
        ),
        max_age: int = MAX_AGE,
    ) -> None:
        self.allowed_events = allowed_events
        self.expected_tokens = expected_tokens
        self.max_age = max_age

    async def process_webhook(self, request: Request) -> BitrixWebhookPayload:
        """
        Основной метод обработки входящего вебхука
        """
        try:
            # Получаем и парсим данные
            payload = await self._parse_webhook_data(request)

            # Валидируем вебхук
            validated_payload = await self._validate_webhook(payload)

            logger.info(
                f"Webhook processed: {validated_payload.event} "
                f"for deal {validated_payload.deal_id}"
            )

            return validated_payload

        except (WebhookValidationError, WebhookSecurityError) as e:
            logger.warning(f"Webhook validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing webhook: {e}")
            raise WebhookValidationError(f"Webhook processing failed: {e}")

    async def _parse_webhook_data(
        self, request: Request
    ) -> BitrixWebhookPayload:
        """
        Парсит form-data и создает объект вебхука
        """
        try:
            form_data = await request.form()
            parsed_body = dict(form_data)

            # Преобразуем плоскую структуру во вложенную
            structured_data = self._flatten_to_nested(parsed_body)

            return BitrixWebhookPayload(**structured_data)

        except ValidationError as e:
            logger.error(f"Webhook data validation failed: {e}")
            raise WebhookValidationError(f"Invalid webhook data: {e}")
        except Exception as e:
            logger.error(f"Failed to parse webhook data: {e}")
            raise WebhookValidationError("Failed to parse webhook data")

    def _flatten_to_nested(self, flat_data: dict[str, Any]) -> dict[str, Any]:
        """
        Преобразует плоскую структуру form-data во вложенный словарь
        """
        result: dict[str, Any] = {}

        for key, value in flat_data.items():
            # Декодируем URL-encoded ключи
            decoded_key = unquote(key)

            if "[" in decoded_key and "]" in decoded_key:
                self._process_nested_key(decoded_key, value, result)
            else:
                result[decoded_key] = value

        return result

    def _process_nested_key(
        self, key: str, value: Any, result: dict[str, Any]
    ) -> None:
        """
        Обрабатывает вложенные ключи вида data[FIELDS][ID]
        """
        parts = key.replace("]", "").split("[")
        current_level = result

        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # Последняя часть - устанавливаем значение
                current_level[part] = value
            else:
                # Промежуточная часть - создаем/получаем вложенный словарь
                if part not in current_level:
                    current_level[part] = {}
                elif not isinstance(current_level[part], dict):
                    # Конфликт типов - перезаписываем значением словарем
                    current_level[part] = {}

                current_level = current_level[part]

    async def _validate_webhook(
        self, payload: BitrixWebhookPayload
    ) -> BitrixWebhookPayload:
        """
        Выполняет полную валидацию вебхука
        """
        # Проверка события
        self._validate_event(payload.event)

        # Проверка безопасности
        self._validate_security(payload.auth, payload.ts)

        return payload

    def _validate_event(self, event: str) -> None:
        """Проверяет разрешенные события"""
        if event not in self.allowed_events:
            raise WebhookValidationError(f"Event '{event}' is not allowed")

    def _validate_security(
        self, auth: BitrixWebhookAuth, timestamp: str
    ) -> None:
        """Выполняет проверки безопасности"""
        # Проверка токена
        if not self._verify_token(auth):
            raise WebhookSecurityError("Invalid webhook token")

        # Проверка временной метки
        if not self._verify_timestamp(timestamp):
            raise WebhookSecurityError("Webhook timestamp is too old")

    def _verify_token(self, auth: BitrixWebhookAuth) -> bool:
        """Проверяет валидность токена вебхука"""
        expected_domain = self.expected_tokens.get(auth.application_token)
        return bool(expected_domain == auth.domain)

    def _verify_timestamp(self, ts: str) -> bool:
        """Проверяет свежесть вебхука"""
        try:
            timestamp = int(ts)
            current_time = int(time.time())
            age = abs(current_time - timestamp)
            return age <= self.max_age
        except ValueError:
            return False
