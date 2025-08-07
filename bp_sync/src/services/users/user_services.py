# from fastapi import Depends

from models.user_models import User as UserDB

from ..base_services.base_service import BaseEntityClient
from .user_bitrix_services import (  # get_user_bitrix_client,
    UserBitrixClient,
)
from .user_repository import UserRepository  # , get_user_repository


class UserClient(BaseEntityClient[UserDB, UserRepository, UserBitrixClient]):
    def __init__(
        self,
        user_bitrix_client: UserBitrixClient,
        user_repo: UserRepository,
    ):
        self._bitrix_client = user_bitrix_client
        self._repo = user_repo

    @property
    def entity_name(self) -> str:
        return "user"

    @property
    def bitrix_client(self) -> UserBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> UserRepository:
        return self._repo


# def get_user_client(
#    user_bitrix_client: UserBitrixClient = Depends(get_user_bitrix_client),
#    user_repo: UserRepository = Depends(get_user_repository),
# ) -> UserClient:
#    return UserClient(user_bitrix_client, user_repo)
