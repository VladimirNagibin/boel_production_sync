from fastapi import APIRouter, Depends

from core.logger import logger
from services.token_storage import get_token_storage, TokenStorage

b24_router = APIRouter()


@b24_router.get(
    "/",
    summary="check redis",
    description="Information about persistency redis.",
)  # type: ignore
async def check(
    token_storage: TokenStorage = Depends(get_token_storage)
) -> dict[str, str]:
    res = await token_storage.get_token("access_token")
    return {"status": res}
