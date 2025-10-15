from fastapi import APIRouter, Depends

from services.dependencies import request_context

from .auth import auth_router
from .deals import deals_router
from .departments import departments_router
from .entities import entity_router
from .products import products_router

b24_router = APIRouter(dependencies=[Depends(request_context)])

# Подключаем все модули
b24_router.include_router(departments_router, prefix="", tags=["departments"])
b24_router.include_router(deals_router, prefix="", tags=["deals"])
b24_router.include_router(auth_router, prefix="", tags=["auth"])
b24_router.include_router(products_router, prefix="", tags=["products"])
b24_router.include_router(entity_router, prefix="", tags=["entities"])
