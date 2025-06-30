import asyncio
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from core.logger import logger
from core.settings import settings


class TokenCipher:
    def __init__(self, encryption_key: str):
        try:
            self.cipher = Fernet(encryption_key.encode())
        except (ValueError, TypeError) as e:
            logger.critical(f"Invalid encryption key: {e}")
            raise RuntimeError("Invalid encryption key configuration") from e

    async def encrypt(self, data: str) -> bytes:
        """Асинхронное шифрование строки в байты"""
        try:
            encrypted_data = await asyncio.to_thread(self._encrypt_sync, data)
            return encrypted_data
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise RuntimeError("Token encryption error") from e

    async def decrypt(self, encrypted_data: bytes) -> str:
        """Асинхронное дешифрование байтов в строку"""
        try:
            decrypted_str = await asyncio.to_thread(
                self._decrypt_sync, encrypted_data
            )
            return decrypted_str
        except InvalidToken as e:
            logger.warning(f"Invalid token decryption attempt: {e}")
            raise ValueError("Invalid or corrupted token") from e
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise RuntimeError("Token decryption error") from e

    def _encrypt_sync(self, data: str) -> bytes:
        return self.cipher.encrypt(  # type: ignore[no-any-return]
            data.encode()
        )

    def _decrypt_sync(self, encrypted_data: bytes) -> str:
        return self.cipher.decrypt(  # type: ignore[no-any-return]
            encrypted_data
        ).decode()


@lru_cache(maxsize=1)
def get_token_cipher() -> TokenCipher:
    """Фабрика для внедрения зависимостей TokenCipher"""
    return TokenCipher(settings.ENCRYPTION_KEY)
