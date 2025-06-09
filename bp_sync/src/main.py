from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from sqladmin import Admin

# from admin.admin_models import ProductAdmin, ProductHSAdmin
# from admin.authenticate import BasicAuthBackend
# from api.v1.health import health_router
# from api.v1.products import product_router
# from api.v1.products_hs import producths_router
from core.logger import LOGGING, logger
from core.settings import settings
from db.postgres import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    ...
    yield
    ...


app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# app.include_router(product_router, prefix="/api/v1/qr", tags=["qr"])
# app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
# app.include_router(producths_router, prefix="/api/v1/hs", tags=["hs"])
# auth_backend = BasicAuthBackend()
# admin = Admin(app, engine, authentication_backend=auth_backend)
# admin.add_view(ProductAdmin)
# admin.add_view(ProductHSAdmin)

if __name__ == "__main__":
    logger.info("Start mark.")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_config=LOGGING,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.APP_RELOAD,
    )
