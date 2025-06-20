from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from core.logger import logger

# from services.bitrix_api_client import BitrixAPIClient
from services.bitrix_clients import BitrixAPIClient1, get_bitrix_client1
from services.bitrix_dependencies import (  # , get_bitrix_client
    get_oauth_client,
)
from services.bitrix_oauth_client import BitrixOAuthClient
from services.exceptions import BitrixAuthError
from services.token_storage import TokenStorage, get_token_storage

b24_router = APIRouter()


@b24_router.get(
    "/",
    summary="check redis",
    description="Information about persistency redis.",
)  # type: ignore
async def check(
    bitrix_client: BitrixAPIClient1 = Depends(get_bitrix_client1),
    token_storage: TokenStorage = Depends(get_token_storage),
) -> JSONResponse:
    res = await bitrix_client.get_deal(50301)
    # await token_storage.delete_token("access_token")
    if res:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "result": res,
            },
        )
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
        logger.exception("Unexpected error during token exchange")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during authentication: {str(e)}",
        )
