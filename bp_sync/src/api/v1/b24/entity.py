import time

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from services.base_services.base_service import BaseEntityClient
from services.companies.company_services import CompanyClient
from services.contacts.contact_services import ContactClient
from services.dependencies import (
    get_company_client_dep,
    get_contact_client_dep,
    get_invoice_client_dep,
    get_lead_client_dep,
    get_user_client_dep,
)
from services.invoices.invoice_services import InvoiceClient
from services.leads.lead_services import LeadClient
from services.users.user_services import UserClient

entity_router = APIRouter(prefix="/entities")


@entity_router.post("/handle-webhook/company")  # type: ignore
async def handle_bitrix24_webhook_company(
    request: Request,
    company_client: CompanyClient = Depends(get_company_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для компаний
    """
    return await _handle_bitrix24_webhook(request, company_client)


@entity_router.post("/handle-webhook/contact")  # type: ignore
async def handle_bitrix24_webhook_contact(
    request: Request,
    contact_client: ContactClient = Depends(get_contact_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для контактов
    """
    return await _handle_bitrix24_webhook(request, contact_client)


@entity_router.post("/handle-webhook/user")  # type: ignore
async def handle_bitrix24_webhook_user(
    request: Request,
    user_client: UserClient = Depends(get_user_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для пользователей
    """
    return await _handle_bitrix24_webhook(request, user_client)


@entity_router.post("/handle-webhook/lead")  # type: ignore
async def handle_bitrix24_webhook_lead(
    request: Request,
    lead_client: LeadClient = Depends(get_lead_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для лидов
    """
    return await _handle_bitrix24_webhook(request, lead_client)


@entity_router.post("/handle-webhook/invoice")  # type: ignore
async def handle_bitrix24_webhook_invoice(
    request: Request,
    invoice_client: InvoiceClient = Depends(get_invoice_client_dep),
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для счетов
    """
    # ENTITY_TYPE_ID = 31
    return await _handle_bitrix24_webhook(
        request, invoice_client  # , ENTITY_TYPE_ID
    )


async def _handle_bitrix24_webhook(
    request: Request,
    entity_client: BaseEntityClient,  # type: ignore[type-arg]
    entity_type_id: int | None = None,
) -> JSONResponse:
    """
    Обработчик вебхуков Bitrix24 для сделок

    - Принимает webhook в формате application/x-www-form-urlencoded
    - Валидирует подпись и данные
    - Обрабатывает тестовые и продакшен сделки
    - Возвращает детализированные ответы
    """
    logger.info(
        f"Received Bitrix24 webhook request for {entity_client.entity_name}"
    )
    try:
        return await entity_client.entity_processing(request, entity_type_id)
    except Exception as e:
        logger.error(
            f"Unhandled error in {entity_client.entity_name} webhook handler: "
            f"{e}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "fail",
                "message": f"{entity_client.entity_name} processing failed",
                "error": str(e),
                "timestamp": time.time(),
            },
        )
