import asyncio
from functools import lru_cache, partial

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
        loop = asyncio.get_event_loop()
        try:
            encrypted_data = await loop.run_in_executor(
                None, partial(self.cipher.encrypt, data.encode())
            )
            return encrypted_data
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise RuntimeError("Token encryption error") from e

    async def decrypt(self, encrypted_data: bytes) -> str:
        """Асинхронное дешифрование байтов в строку"""
        loop = asyncio.get_event_loop()
        try:
            decrypted_bytes = await loop.run_in_executor(
                None, partial(self.cipher.decrypt, encrypted_data)
            )
            return decrypted_bytes.decode()
        except InvalidToken as e:
            logger.warning(f"Invalid token decryption attempt: {e}")
            raise ValueError("Invalid or corrupted token") from e
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise RuntimeError("Token decryption error") from e


@lru_cache(maxsize=1)
def get_token_cipher() -> TokenCipher:
    """Фабрика для внедрения зависимостей TokenCipher"""
    return TokenCipher(settings.ENCRYPTION_KEY)
