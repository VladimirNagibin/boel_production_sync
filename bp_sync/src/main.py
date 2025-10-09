from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aredis
import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from sqladmin import Admin

from admin.admin_models import register_models
from admin.authenticate import BasicAuthBackend
from api.v1.accounting_documents import account_router
from api.v1.b24.b24_router import b24_router
from api.v1.messages import messages_router
from api.v1.reports import reports_router
from api.v1.test import test_router
from api.v1.upload_product_codes import upload_codes_router
from core.logger import LOGGING, logger
from core.settings import settings
from db import redis
from db.postgres import engine
from services.rabbitmq_client import get_rabbitmq

# from cryptography.fernet import Fernet
# new_key = Fernet.generate_key()

# Преобразовать в строку для хранения
# key_str = new_key.decode('utf-8')
# print("Сгенерированный ключ:", key_str)


async def _init_redis() -> None:
    redis.redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        ssl=False,
    )
    try:
        await redis.redis.ping()
        logger.info("Успешное подключение к Redis.")
    except aredis.AuthenticationError:
        logger.error("Ошибка аутентификации: неверный пароль Redis")
        raise
    except aredis.ConnectionError:
        logger.error("Не удалось подключиться к Redis")
        raise


async def _shutdown_redis() -> None:
    if redis.redis:
        await redis.redis.save()
        await redis.redis.aclose()


async def _init_rabbitmq() -> None:
    rabbitmq_client = get_rabbitmq()
    await rabbitmq_client.startup()


async def _shutdown_rabbitmq() -> None:
    rabbitmq_client = get_rabbitmq()
    await rabbitmq_client.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _init_redis()
    await _init_rabbitmq()
    yield
    await _shutdown_redis()
    await _shutdown_rabbitmq()


def start_server() -> None:
    logger.info("Start bp_sync.")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_config=LOGGING,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.APP_RELOAD,
    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(b24_router, prefix="/api/v1/b24", tags=["b24"])
app.include_router(
    messages_router, prefix="/api/v1/messages", tags=["messages_rabbitmq"]
)
app.include_router(
    reports_router,
    prefix="/api/v1/reports",
    tags=["reports"],
)
app.include_router(
    upload_codes_router,
    prefix="/api/v1/codes",
    tags=["product_codes_1C"],
)
app.include_router(
    account_router,
    prefix="/api/v1/account",
    tags=["account"],
)
app.include_router(test_router, prefix="/api/v1/test", tags=["test"])

auth_backend = BasicAuthBackend()
admin = Admin(
    app,
    engine,
    title="Админка",
    templates_dir="templates/admin",
    authentication_backend=auth_backend,
)
register_models(admin)


if __name__ == "__main__":
    start_server()
