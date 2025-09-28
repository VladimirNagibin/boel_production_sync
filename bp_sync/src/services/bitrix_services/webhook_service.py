import time

from fastapi import Depends, HTTPException, status

from core.settings import settings
from schemas.deal_schemas import BitrixWebhookAuth, BitrixWebhookPayload

MAX_AGE = 300


class WebhookService:
    """Сервис для обработки вебхуков Bitrix24"""

    @staticmethod
    def verify_token(auth: BitrixWebhookAuth) -> bool:
        """Проверка токена вебхука"""
        expected_domain = settings.web_hook_config["expected_tokens"].get(
            auth.application_token
        )
        return bool(expected_domain == auth.domain)

    @staticmethod
    def verify_timestamp(ts: str, max_age: int = MAX_AGE) -> bool:
        """Проверка свежести вебхука (защита от replay атак)"""
        try:
            timestamp = int(ts)
            current_time = int(time.time())
            return abs(current_time - timestamp) <= max_age
        except ValueError:
            return False


def get_webhook_service() -> WebhookService:
    return WebhookService()


async def verify_webhook(
    payload: BitrixWebhookPayload,
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> BitrixWebhookPayload:
    """Проверка валидности вебхука"""

    # Проверка события
    if payload.event not in settings.web_hook_config["allowed_events"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Event not allowed"
        )

    # Проверка токена
    if not webhook_service.verify_token(payload.auth):
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    # Проверка временной метки
    if not webhook_service.verify_timestamp(payload.ts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook timestamp is too old",
        )

    return payload
