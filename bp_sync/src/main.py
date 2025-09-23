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

# from api.v1.health import health_router
# from api.v1.products import product_router
from api.v1.b24 import b24_router
from api.v1.reports import reports_router
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

# rabbitmq_client = RabbitMQClient()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis.redis = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        ssl=False,  # Для продакшена используйте True
    )
    rabbitmq_client = get_rabbitmq()
    await rabbitmq_client.startup()
    try:
        # Проверка подключения и аутентификации
        await redis.redis.ping()
        print("✅ Успешное подключение к Redis")
    except aredis.AuthenticationError:
        print("❌ Ошибка аутентификации: неверный пароль Redis")
        raise
    except aredis.ConnectionError:
        print("❌ Не удалось подключиться к Redis")
        raise
    yield
    await redis.redis.save()
    await redis.redis.aclose()
    rabbitmq_client = get_rabbitmq()
    await rabbitmq_client.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(b24_router, prefix="/api/v1/b24", tags=["b24"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(upload_codes_router, prefix="/api/v1/codes", tags=["codes"])
# app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
# app.include_router(producths_router, prefix="/api/v1/hs", tags=["hs"])
auth_backend = BasicAuthBackend()
admin = Admin(app, engine, authentication_backend=auth_backend)
register_models(admin)

if __name__ == "__main__":
    logger.info("Start bp_sync.")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_config=LOGGING,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.APP_RELOAD,
    )
