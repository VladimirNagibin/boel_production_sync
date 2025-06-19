from functools import lru_cache
from typing import Literal

from fastapi import Depends
from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.logger import logger
from core.settings import settings
from db.redis import get_redis
from .token_cipher import get_token_cipher, TokenCipher

TokenType = Literal["refresh_token", "access_token"]
DEFAULT_REFRESH_TTL = 15_552_000  # 180 дней в секундах


class TokenStorage:
    def __init__(self, redis: Redis, token_cipher: TokenCipher):
        self.redis = redis
        self.token_cipher = token_cipher

    async def save_token(
        self,
        token: str,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
        expire_seconds: int = DEFAULT_REFRESH_TTL
    ) -> None:
        """Сохраняет токен с шифрованием и TTL"""
        key = f"{token_type}:{user_id}:{provider}"
        try:
            encrypted_token = await self.token_cipher.encrypt(token)
            await self.redis.set(
                name=key,
                value=encrypted_token,
                ex=expire_seconds
            )
            logger.debug(f"Token saved for {key}, TTL: {expire_seconds}s")
        except RedisError as e:
            logger.error(f"Redis save error for {key}: {e}")
            raise ConnectionError("Token storage unavailable") from e
        except Exception as e:
            logger.error(f"Unexpected save error for {key}: {e}")
            raise RuntimeError("Token save operation failed") from e

    async def get_token(
        self,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24
    ) -> str | None:
        """Получает и расшифровывает токен"""
        key = f"{token_type}:{user_id}:{provider}"
        try:
            encrypted_token = await self.redis.get(key)
            if not encrypted_token:
                logger.debug(f"Token not found for {key}")
                return None
            return await self.token_cipher.decrypt(encrypted_token)
        except RedisError as e:
            logger.error(f"Redis get error for {key}: {e}")
            raise ConnectionError("Token retrieval failed") from e
        except Exception as e:
            logger.error(f"Unexpected get error for {key}: {e}")
            return None

    async def delete_token(
        self,
        token_type: TokenType,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24
    ) -> bool:
        """Удаляет токен из хранилища"""
        key = f"{token_type}:{user_id}:{provider}"
        try:
            deleted = await self.redis.delete(key)
            success = deleted > 0
            if success:
                logger.debug(f"Token deleted for {key}")
            else:
                logger.debug(f"Token not found for deletion: {key}")
            return success
        except RedisError as e:
            logger.error(f"Redis delete error for {key}: {e}")
            raise ConnectionError("Token deletion failed") from e
        except Exception as e:
            logger.error(f"Unexpected delete error for {key}: {e}")
            return False


@lru_cache(maxsize=1)
def get_token_storage(
    redis: Redis = Depends(get_redis),
    token_cipher: TokenCipher = Depends(get_token_cipher)
) -> TokenStorage:
    """Фабрика для внедрения зависимостей TokenStorage"""
    return TokenStorage(redis, token_cipher)
