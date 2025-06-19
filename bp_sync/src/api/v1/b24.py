from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from core.logger import logger
from services.token_storage import get_token_storage, TokenStorage
from bp_sync.src.services.bitrix_clients import get_bitrix_client, BitrixAPIClient

b24_router = APIRouter()


@b24_router.get(
    "/",
    summary="check redis",
    description="Information about persistency redis.",
)  # type: ignore
async def check(
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
    token_storage: TokenStorage = Depends(get_token_storage),
):
    res = await bitrix_client.get_deal(50301)
    # await token_storage.delete_token("access_token")
    if res:
        return {"result": res}


@b24_router.get("/auth/callback")
async def handle_callback(
    code: str | None = None,
    error: str | None = None,
    bitrix_client: BitrixAPIClient = Depends(get_bitrix_client),
):
    if error:
        return {"error": error}

    if not code:
        return {"error": "Authorization code missing"}

    # Здесь можно обменять code на токен
    return {"code": await bitrix_client.fetch_token(code)}
