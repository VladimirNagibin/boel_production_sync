import os
from datetime import timedelta
from cryptography.fernet import Fernet
from redis.asyncio import Redis

from core.settings import settings


class TokenStorage:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())

    def _encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def _decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()

    def save_refresh_token(
        self,
        refresh_token: str,
        user_id: str = str(settings.SERVICE_USER),
        provider: str = settings.PROVIDER_B24,
    ):
        """Сохраняет токен с шифрованием"""
        key = f"refresh_token:{user_id}:{provider}"
        refresh = self._encrypt(refresh_token)

        self.redis.hset(key, refresh)

    def get_tokens(self, user_id: str, provider: str) -> dict:
        """Получает и расшифровывает токены"""
        key = f"external_tokens:{user_id}:{provider}"
        data = self.redis.hgetall(key)

        if not data:
            return None

        return {
            "access_token": self._decrypt(data[b"access"]),
            "refresh_token": self._decrypt(data[b"refresh"]),
        }





    def save_tokens(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: str,
        expires_in: int
    ):
        """Сохраняет токены с TTL и шифрованием"""
        key = f"external_tokens:{user_id}:{provider}"

        # Шифруем токены
        encrypted_data = {
            "access": self._encrypt(access_token),
            "refresh": self._encrypt(refresh_token),
        }

        # Сохраняем в Redis с TTL (expires_in + буфер)
        self.redis.hset(key, mapping=encrypted_data)
        self.redis.expire(key, timedelta(seconds=expires_in + 300))

    def get_tokens(self, user_id: str, provider: str) -> dict:
        """Получает и расшифровывает токены"""
        key = f"external_tokens:{user_id}:{provider}"
        data = self.redis.hgetall(key)

        if not data:
            return None

        return {
            "access_token": self._decrypt(data[b"access"]),
            "refresh_token": self._decrypt(data[b"refresh"]),
        }

    def delete_tokens(self, user_id: str, provider: str):
        key = f"external_tokens:{user_id}:{provider}"
        self.redis.delete(key)
