from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aredis
import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

# from admin.admin_models import ProductAdmin, ProductHSAdmin
# from admin.authenticate import BasicAuthBackend
# from api.v1.health import health_router
# from api.v1.products import product_router
from api.v1.b24 import b24_router
from core.logger import LOGGING, logger
from core.settings import settings
from db import redis

# from sqladmin import Admin


# from db.postgres import engine

# from cryptography.fernet import Fernet
# new_key = Fernet.generate_key()

# Преобразовать в строку для хранения
# key_str = new_key.decode('utf-8')
# print("Сгенерированный ключ:", key_str)


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


app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(b24_router, prefix="/api/v1/b24", tags=["b24"])
# app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
# app.include_router(producths_router, prefix="/api/v1/hs", tags=["hs"])
# auth_backend = BasicAuthBackend()
# admin = Admin(app, engine, authentication_backend=auth_backend)
# admin.add_view(ProductAdmin)
# admin.add_view(ProductHSAdmin)

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
