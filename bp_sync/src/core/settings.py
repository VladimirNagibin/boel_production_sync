from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore
    PROJECT_NAME: str = "bp_sync"
    APP_RELOAD: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5442
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "bp_sync"
    POSTGRES_DB_ECHO: bool = True
    SERVICE_USER: int
    PROVIDER_B24: str = "B24"

    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    USER_ADMIN: str = "admin"
    PASS_ADMIN: str = "pass"

    BITRIX_LOGIN: str
    BITRIX_PASS: str
    BITRIX_CLIENT_ID: str
    BITRIX_CLIENT_SECRET: str
    BITRIX_PORTAL: str
    BITRIX_REDIRECT_URI: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    ENCRYPTION_KEY: str = (
        "your_fernet_key_here"  # сгенерировать Fernet.generate_key()
    )

    BASE_DIR: str = str(Path(__file__).resolve().parent.parent)
    LOGGING_FILE_MAX_BYTES: int = 500_000

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
