from functools import lru_cache

from cryptography.fernet import Fernet
from fastapi import Depends
from redis.asyncio import Redis

from core.settings import settings
from db.redis import get_redis


class TokenStorage:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())

    def _encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def _decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()

    async def save_token(
        self,
        token: str,
        token_type: str,  # refresh_token, access_token
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
        expires_in: int = 15_552_000  # 180 дней refresh / 1 час access
    ) -> None:
        """Сохраняет токен с шифрованием"""
        key = f"{token_type}:{user_id}:{provider}"
        encrypted_token = self._encrypt(token)

        await self.redis.set(
            name=key,
            value=encrypted_token,
            ex=expires_in
        )

    async def get_token(
        self,
        token_type: str,  # refresh_token, access_token
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24
    ) -> str | None:
        """Получает и расшифровывает токен"""
        key = f"{token_type}:{user_id}:{provider}"
        encrypted_token = await self.redis.get(key)

        if not encrypted_token:
            return None

        return self._decrypt(encrypted_token)

    async def delete_token(
        self,
        token_type: str,  # refresh_token, access_token
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24
    ):
        """Удаляет токен из хранилища"""
        key = f"{token_type}:{user_id}:{provider}"
        await self.redis.delete(key)


@lru_cache()
def get_token_storage(
    redis: Redis = Depends(get_redis),
) -> TokenStorage:
    return TokenStorage(redis)
