from fastapi import APIRouter, Depends

from services.dependencies import request_context

from .auth import auth_router
from .deals import deals_router
from .departments import departments_router
from .messages import messages_router

b24_router = APIRouter(dependencies=[Depends(request_context)])

# Подключаем все модули
b24_router.include_router(
    departments_router, prefix="/b24", tags=["departments"]
)
b24_router.include_router(deals_router, prefix="/b24", tags=["deals"])
b24_router.include_router(
    messages_router, prefix="/b24", tags=["messages_rabbitmq"]
)
b24_router.include_router(auth_router, prefix="/b24", tags=["auth"])
