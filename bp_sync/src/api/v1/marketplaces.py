"""Роуты для синхронизации заказов маркетплейсов со сделками."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from models.enums import MarketplaceEnum
from schemas.marketplace_schemas import MarketplaceSyncRequest
from services.dependencies import (
    get_marketplace_service_dep,
    request_context,
)
from services.marketplaces.marketplace_services import MarketplaceService

from .deps import verify_api_key

marketplaces_router = APIRouter(dependencies=[Depends(request_context)])


@marketplaces_router.post(
    "/sync",
    summary="Запустить синхронизацию заказов",
    description="Загружает заказы из маркетплейсов и синхронизирует сделки.",
)
async def trigger_marketplace_sync(
    request: MarketplaceSyncRequest,
    marketplace_service: MarketplaceService = Depends(
        get_marketplace_service_dep
    ),
    _: str = Depends(verify_api_key),
) -> JSONResponse:
    """Запускает синхронизацию заказов маркетплейсов."""
    try:
        result = await marketplace_service.sync_accounts(request.since)
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
    except Exception as exc:
        logger.error("Ошибка синхронизации маркетплейсов: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@marketplaces_router.post(
    "/webhook/{provider}",
    summary="Обработать вебхук маркетплейса",
    description="Принимает push-уведомление о заказе из маркетплейса.",
)
async def marketplace_webhook(
    provider: MarketplaceEnum,
    request: Request,
    marketplace_service: MarketplaceService = Depends(
        get_marketplace_service_dep
    ),
) -> JSONResponse:
    """Обрабатывает входящий вебхук маркетплейса."""
    try:
        result = await marketplace_service.handle_webhook(provider, request)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "result": result},
        )
    except Exception as exc:
        logger.error(
            "Ошибка вебхука маркетплейса %s: %s", provider, exc
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": str(exc)},
        )


@marketplaces_router.get(
    "/orders",
    summary="Список заказов маркетплейсов",
    description="Возвращает заказы со статусами синхронизации.",
)
async def list_marketplace_orders(
    account_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, le=1000),
    marketplace_service: MarketplaceService = Depends(
        get_marketplace_service_dep
    ),
    _: str = Depends(verify_api_key),
) -> JSONResponse:
    """Возвращает список заказов маркетплейсов."""
    orders = await marketplace_service.repository.list_orders(
        account_id=account_id, limit=limit
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "orders": [
                {
                    "id": str(order.id),
                    "marketplace": order.marketplace,
                    "external_order_id": order.external_order_id,
                    "status": order.status,
                    "sync_status": order.sync_status,
                    "deal_id": order.deal_id,
                    "last_error": order.last_error,
                }
                for order in orders
            ]
        },
    )


@marketplaces_router.get(
    "/sync-runs",
    summary="История запусков синхронизации",
    description="Возвращает историю запусков синхронизации маркетплейсов.",
)
async def list_sync_runs(
    limit: int = Query(100, le=1000),
    marketplace_service: MarketplaceService = Depends(
        get_marketplace_service_dep
    ),
    _: str = Depends(verify_api_key),
) -> JSONResponse:
    """Возвращает историю запусков синхронизации."""
    runs = await marketplace_service.repository.list_sync_runs(limit=limit)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "runs": [
                {
                    "id": str(run.id),
                    "marketplace": run.marketplace,
                    "account_id": (
                        str(run.account_id) if run.account_id else None
                    ),
                    "status": run.status,
                    "started_at": run.started_at.isoformat(),
                    "finished_at": (
                        run.finished_at.isoformat()
                        if run.finished_at
                        else None
                    ),
                    "orders_processed": run.orders_processed,
                    "orders_created": run.orders_created,
                    "orders_updated": run.orders_updated,
                    "orders_with_error": run.orders_with_error,
                }
                for run in runs
            ]
        },
    )
