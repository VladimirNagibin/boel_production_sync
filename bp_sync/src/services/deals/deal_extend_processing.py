from typing import Any

import httpx
from fastapi import HTTPException

from core.logger import logger
from core.settings import settings

TIMEOUT = 30.0


class DealProcessingClient:
    def __init__(self) -> None:
        self.php_endpoint_url = (
            f"{settings.WEB_HOOK_PORTAL}/{settings.ENDPOINT_SEND_DEAL_STATUS}"
        )
        self.timeout = TIMEOUT

    async def send_deal_processing_request(
        self, deal_id: int, timestamp: int
    ) -> dict[str, Any]:
        """
        Отправляет запрос на PHP endpoint для обработки сделки

        Args:
            deal_id: ID сделки
            timestamp: Временная метка

        Returns:
            Ответ от PHP сервера
        """
        payload = {"deal_id": deal_id, "timestamp": timestamp}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.php_endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    return response.json()  # type: ignore[no-any-return]
                else:
                    logger.error(
                        f"PHP endpoint error: {response.status_code} - "
                        f"{response.text}"
                    )
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"PHP endpoint error: {response.text}",
                    )

        except httpx.TimeoutException:
            logger.error(
                f"Timeout while calling PHP endpoint for deal {deal_id}"
            )
            raise HTTPException(status_code=504, detail="PHP endpoint timeout")
        except httpx.RequestError as e:
            logger.error(f"Request error to PHP endpoint: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to PHP endpoint: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )


async def get_deal_processing_client() -> DealProcessingClient:
    return DealProcessingClient()
