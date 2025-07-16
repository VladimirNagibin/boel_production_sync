from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from core.logger import logger

# from services.bitrix_api_client import BitrixAPIClient
from schemas.contact_schemas import ContactUpdate

# from schemas.deal_schemas import DealUpdate
# from schemas.lead_schemas import LeadUpdate
from services.bitrix_services.bitrix_oauth_client import BitrixOAuthClient
from services.contacts.contact_bitrix_services import (
    ContactBitrixClient,
    get_contact_bitrix_client,
)
from services.deals.deal_bitrix_services import (
    DealBitrixClient,
    get_deal_bitrix_client,
)
from services.deals.deal_services import (
    DealClient,
    get_deal_client,
)
from services.dependencies import (  # , get_bitrix_client
    get_oauth_client,
)
from services.exceptions import BitrixAuthError
from services.leads.lead_bitrix_services import (
    LeadBitrixClient,
    get_lead_bitrix_client,
)
from services.leads.lead_services import (  # LeadClient,
    get_lead_client,
)
from services.token_services.token_storage import (
    TokenStorage,
    get_token_storage,
)

b24_router = APIRouter()


@b24_router.get(
    "/",
    summary="check redis",
    description="Information about persistency redis.",
)  # type: ignore
async def check(
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    deal_client: DealClient = Depends(get_deal_client),
    lead_client: DealClient = Depends(get_lead_client),
    lead_bitrix_client: LeadBitrixClient = Depends(get_lead_bitrix_client),
    contact_bitrix_client: ContactBitrixClient = Depends(
        get_contact_bitrix_client
    ),
    token_storage: TokenStorage = Depends(get_token_storage),
) -> JSONResponse:
    res = await contact_bitrix_client.get(13493)
    res2 = ContactUpdate(**res.model_dump(by_alias=True, exclude_unset=True))
    # print(du.to_bitrix_dict())
    res3 = await contact_bitrix_client.update(res2)  # 60131)
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
    print(res3)
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
