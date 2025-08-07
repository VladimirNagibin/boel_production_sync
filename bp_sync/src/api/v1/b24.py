import time
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from core.logger import logger

# from schemas.deal_schemas import DealUpdate
# from schemas.lead_schemas import LeadUpdate
from services.bitrix_services.bitrix_oauth_client import BitrixOAuthClient
from services.deals.deal_bitrix_services import (
    DealBitrixClient,
)
from services.deals.deal_services import (
    DealClient,
)
from services.dependencies import (
    get_deal_bitrix_client_dep,
    get_deal_client_dep,
    get_department_client_dep,
    get_oauth_client,
    request_context,
)
from services.entities.department_services import (
    DepartmentClient,
)
from services.exceptions import BitrixAuthError

# from services.bitrix_api_client import BitrixAPIClient
# from schemas.contact_schemas import ContactUpdate
# from services.bitrix_services.bitrix_api_client import BitrixAPIClient


b24_router = APIRouter(dependencies=[Depends(request_context)])


@b24_router.get(
    "/update-departments",
    summary="update departments",
    description="Update departments.",
)  # type: ignore
async def update_departments(
    department_client: DepartmentClient = Depends(get_department_client_dep),
) -> JSONResponse:

    result = await department_client.import_from_bitrix()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "updated": len(result),
        },
    )


@b24_router.get(
    "/load-deals",
    summary="load deals",
    description="Load deals for period.",
)  # type: ignore
async def load_deals(
    start_data: date,
    end_data: date,
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client_dep),
    deal_client: DealClient = Depends(get_deal_client_dep),
) -> JSONResponse:
    # Рассчитываем конец периода как начало следующего дня
    end_date_plus_one = end_data + timedelta(days=1)

    # Форматируем даты для Bitrix API
    start_str = start_data.strftime("%Y-%m-%d 00:00:00")
    end_str = end_date_plus_one.strftime("%Y-%m-%d 00:00:00")

    filter_entity: dict[str, Any] = {
        ">=BEGINDATE": start_str,
        "<BEGINDATE": end_str,
        "CATEGORY_ID": 0,
    }

    # Получаем сделки с пагинацией
    all_deals = []
    select = ["ID"]
    start = 0

    while True:
        res = await deal_bitrix_client.list(
            select=select, filter_entity=filter_entity, start=start
        )
        if not res:
            break
        deals = res.result
        # total = res.total
        next = res.next
        all_deals.extend(deals)
        if next:
            start = next
        else:
            break
        # Прерываем цикл, если получено меньше 50 записей (последняя страница)
        # if len(deals) < 50:
        #    break
        time.sleep(2)
    # Извлекаем только ID сделок
    deal_ids: list[int | None] = [deal.external_id for deal in all_deals]
    print(deal_ids)
    for deal_id in deal_ids:
        print(f"{deal_id}====================================")
        if deal_id:
            await deal_client.import_from_bitrix(deal_id)
        time.sleep(2)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"deal_ids": deal_ids, "count": len(deal_ids)},
    )


@b24_router.get(
    "/",
    summary="check redis",
    description="Information about persistency redis.",
)  # type: ignore
async def check(
    department_client: DepartmentClient = Depends(get_department_client_dep),
    # bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
    # deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    # user_bitrix_client: UserBitrixClient = Depends(get_user_bitrix_client),
    # invoice_bitrix_client: InvoiceBitrixClient = Depends(
    #    get_invoice_bitrix_client
    # ),
    # deal_client: DealClient = Depends(get_deal_client),
    # lead_client: DealClient = Depends(get_lead_client),
    # lead_bitrix_client: LeadBitrixClient = Depends(get_lead_bitrix_client),
    # contact_bitrix_client: ContactBitrixClient = Depends(
    #    get_contact_bitrix_client
    # ),
    # token_storage: TokenStorage = Depends(get_token_storage),
) -> JSONResponse:

    # res = await deal_client.import_from_bitrix(50301)
    res = await department_client.import_from_bitrix()
    # res = await deal_bitrix_client.get(51463)
    # res2 = ContactUpdate(**res.model_dump(by_alias=True, exclude_unset=True))
    # print(du.to_bitrix_dict())
    # res3 = await contact_bitrix_client.update(res2)  # 60131)
    # res = await deal_client.refresh_from_bitrix(51975)  # 60131)
    # lead = await lead_bitrix_client.get(59773)
    # res2 = DealUpdate(**res.model_dump(by_alias=True, exclude_unset=True))
    # lead2 = LeadUpdate(**lead.model_dump(by_alias=True, exclude_unset=True))

    # lead2.title = "NEW TEST 2"
    # lead2.phone[0].value_type = "MOBILE"
    # lead2.phone[1].value = "777777777777"
    # res2.shipping_type = 517
    # res2 = LeadUpdate(title="QWERTY")
    # res3 = await lead_bitrix_client.update(lead2)
    # print(res2.title)
    # res3 = await deal_bitrix_client.list(
    #    filter_entity={"ID": 51463},
    #    select=["ID", "TITLE", "OPPORTUNITY"],
    #    start=0,
    # )
    print(res)
    # await token_storage.delete_token("access_token")
    # if res3:
    #     deal_create = DealCreate(**res)
    #     print(res.model_dump())
    #    return JSONResponse(
    #        status_code=status.HTTP_200_OK,
    #        content={
    #            "status": "success",
    #            "bool": [str(type(res)) for res in res3],
    #            # "result": res.to_bitrix_dict(),
    #        },
    #    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": "fault",
        },
    )


@b24_router.get(
    "/auth/callback", summary="OAuth 2.0 Callback Handler"
)  # type: ignore
async def handle_auth_callback(
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    oauth_client: BitrixOAuthClient = Depends(get_oauth_client),
) -> JSONResponse:
    """
    Handle Bitrix24 OAuth 2.0 callback

    Processes authorization code or error returned from Bitrix24 OAuth server.
    """
    if error or error_description:
        error_msg = error_description or error or "Unknown OAuth error"
        logger.error(f"OAuth callback error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
        )

    if not code:
        logger.warning(
            "Authorization callback received without code parameter"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required",
        )
    try:
        # Обмен кода на токены
        access_token = await oauth_client.fetch_token(code)
        logger.info("Successfully obtained access token from Bitrix24")

        # Формирование успешного ответа (без передачи самого токена)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Authentication completed successfully",
                "access_token_obtained": bool(access_token),
            },
        )

    except BitrixAuthError as auth_error:
        logger.error(f"Authentication failed: {str(auth_error)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(auth_error)
        )

    except Exception as e:
        logger.exception(f"Unexpected error during token exchange: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during authentication: {str(e)}",
        )
