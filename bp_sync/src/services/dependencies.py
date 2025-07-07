from fastapi import Depends

from core.settings import settings

from .bitrix_services.bitrix_api_client import BitrixAPIClient
from .bitrix_services.bitrix_oauth_client import BitrixOAuthClient
from .token_services.token_storage import TokenStorage, get_token_storage


def get_oauth_client(
    token_storage: TokenStorage = Depends(get_token_storage),
) -> BitrixOAuthClient:
    return BitrixOAuthClient(
        portal_domain=settings.BITRIX_PORTAL,
        client_id=settings.BITRIX_CLIENT_ID,
        client_secret=settings.BITRIX_CLIENT_SECRET,
        redirect_uri=settings.BITRIX_REDIRECT_URI,
        token_storage=token_storage,
    )


def get_bitrix_client(
    oauth_client: BitrixOAuthClient = Depends(get_oauth_client),
) -> BitrixAPIClient:
    return BitrixAPIClient(oauth_client)
