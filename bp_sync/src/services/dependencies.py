import inspect
from contextvars import ContextVar
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Type,
    TypeVar,
    cast,
)

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from core.settings import settings
from db.postgres import get_session
from db.redis import get_redis

from .billings.billing_repository import BillingRepository
from .bitrix_services.bitrix_api_client import BitrixAPIClient
from .bitrix_services.bitrix_oauth_client import BitrixOAuthClient
from .companies.company_bitrix_services import CompanyBitrixClient
from .companies.company_repository import CompanyRepository
from .companies.company_services import CompanyClient
from .contacts.contact_bitrix_services import ContactBitrixClient
from .contacts.contact_repository import ContactRepository
from .contacts.contact_services import ContactClient
from .deals.deal_bitrix_services import DealBitrixClient
from .deals.deal_repository import DealRepository
from .deals.deal_services import DealClient
from .delivery_notes.delivery_note_repository import DeliveryNoteRepository
from .entities.department_services import DepartmentClient
from .entities.source_services import SourceClient
from .invoices.invoice_bitrix_services import InvoiceBitrixClient
from .invoices.invoice_repository import InvoiceRepository
from .invoices.invoice_services import InvoiceClient
from .leads.lead_bitrix_services import LeadBitrixClient
from .leads.lead_repository import LeadRepository
from .leads.lead_services import LeadClient
from .products.product_bitrix_services import ProductBitrixClient
from .timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from .timeline_comments.timeline_comment_repository import (
    TimelineCommentRepository,
)
from .token_services.token_cipher import TokenCipher
from .token_services.token_storage import TokenStorage
from .users.user_bitrix_services import UserBitrixClient
from .users.user_repository import UserRepository
from .users.user_services import UserClient

ModelBase = TypeVar("ModelBase", bound=DeclarativeBase)

# Контекстная переменная для хранения текущей сессии базы данных
_session_ctx: ContextVar[AsyncSession | None] = ContextVar(
    "_session_ctx", default=None
)
# Контекстная переменная для хранения созданных сервисов с проверкой на повтор
_services_cache_ctx: ContextVar[dict[str, Any]] = ContextVar(
    "_services_cache", default={}
)
# Контекстная переменная для хранения проверенных объектов на существование в
# рамках запроса
_exists_cache_ctx: ContextVar[
    dict[tuple[Type[Any], tuple[tuple[str, Any], ...]], bool]
] = ContextVar("_exists_cache", default={})
# Контекстная переменная для хранения проверенных объектов на существование
# либо созданных в рамках запроса
_updated_cache_ctx: ContextVar[set[tuple[Type[Any], int | str]]] = ContextVar(
    "_updated_cache", default=set()
)
# Глобальный кэш для отслеживания создания сущностей в текущем контексте
_creation_cache_ctx: ContextVar[dict[tuple[Type[Any], int | str], bool]] = (
    ContextVar("creation_cache", default={})
)

# Кэш для отслеживания сущностей, требующих обновления
_update_needed_cache_ctx: ContextVar[set[tuple[Type[Any], int | str]]] = (
    ContextVar("update_needed_cache", default=set())
)


def get_session_context() -> AsyncSession:
    """Получает текущую сессию из контекста"""
    session = _session_ctx.get()
    if session is None:
        raise RuntimeError("Session context is not set")
    return session


class ServiceLocator:
    async def get(self, service_name: str) -> Any:
        return await get_service(service_name)


# Явные фабрики для создания сервисов
async def create_token_storage() -> TokenStorage:
    redis: Redis | None = await get_redis()
    if redis:
        return TokenStorage(redis, TokenCipher(settings.ENCRYPTION_KEY))
    raise RuntimeError("Redis is not initialized")


async def create_oauth_client() -> BitrixOAuthClient:
    return BitrixOAuthClient(
        portal_domain=settings.BITRIX_PORTAL,
        client_id=settings.BITRIX_CLIENT_ID,
        client_secret=settings.BITRIX_CLIENT_SECRET,
        redirect_uri=settings.BITRIX_REDIRECT_URI,
        token_storage=await create_token_storage(),
    )


async def create_bitrix_client() -> BitrixAPIClient:
    oauth_client = await create_oauth_client()
    return BitrixAPIClient(oauth_client)


async def create_user_bitrix_client() -> UserBitrixClient:
    return UserBitrixClient(await create_bitrix_client())


async def create_user_repository() -> UserRepository:
    return UserRepository(get_session_context())


async def create_user_client() -> UserClient:
    return UserClient(
        user_bitrix_client=await create_user_bitrix_client(),
        user_repo=await create_user_repository(),
    )


async def create_lead_bitrix_client() -> LeadBitrixClient:
    return LeadBitrixClient(await create_bitrix_client())


async def create_lead_repository() -> LeadRepository:
    locator = ServiceLocator()
    return LeadRepository(
        session=get_session_context(),
        get_company_client=lambda: locator.get("company_client"),
        get_contact_client=lambda: locator.get("contact_client"),
        get_user_client=lambda: locator.get("user_client"),
        get_source_client=lambda: locator.get("source_client"),
    )


async def create_lead_client() -> LeadClient:
    return LeadClient(
        lead_bitrix_client=await create_lead_bitrix_client(),
        lead_repo=await create_lead_repository(),
    )


async def create_invoice_bitrix_client() -> InvoiceBitrixClient:
    return InvoiceBitrixClient(await create_bitrix_client())


async def create_invoice_repository() -> InvoiceRepository:
    locator = ServiceLocator()
    return InvoiceRepository(
        session=get_session_context(),
        get_company_client=lambda: locator.get("company_client"),
        get_contact_client=lambda: locator.get("contact_client"),
        get_deal_client=lambda: locator.get("deal_client"),
        get_user_client=lambda: locator.get("user_client"),
        get_source_client=lambda: locator.get("source_client"),
    )


async def create_invoice_client() -> InvoiceClient:
    return InvoiceClient(
        invoice_bitrix_client=await create_invoice_bitrix_client(),
        invoice_repo=await create_invoice_repository(),
    )


async def create_department_client() -> DepartmentClient:
    return DepartmentClient(
        bitrix_client=await create_bitrix_client(),
        session=get_session_context(),
    )


async def create_source_client() -> SourceClient:
    return SourceClient(get_session_context())


async def create_delivery_note_repository() -> DeliveryNoteRepository:
    locator = ServiceLocator()
    return DeliveryNoteRepository(
        session=get_session_context(),
        get_company_client=lambda: locator.get("company_client"),
        get_invoice_client=lambda: locator.get("invoice_client"),
        get_user_client=lambda: locator.get("user_client"),
    )


async def create_deal_bitrix_client() -> DealBitrixClient:
    return DealBitrixClient(await create_bitrix_client())


async def create_deal_repository() -> DealRepository:
    locator = ServiceLocator()
    return DealRepository(
        session=get_session_context(),
        get_company_client=lambda: locator.get("company_client"),
        get_contact_client=lambda: locator.get("contact_client"),
        get_lead_client=lambda: locator.get("lead_client"),
        get_user_client=lambda: locator.get("user_client"),
        get_source_client=lambda: locator.get("source_client"),
    )


async def create_deal_client() -> DealClient:
    return DealClient(
        deal_bitrix_client=await create_deal_bitrix_client(),
        deal_repo=await create_deal_repository(),
    )


async def create_contact_bitrix_client() -> ContactBitrixClient:
    return ContactBitrixClient(await create_bitrix_client())


async def create_contact_repository() -> ContactRepository:
    locator = ServiceLocator()
    return ContactRepository(
        session=get_session_context(),
        get_company_client=lambda: locator.get("company_client"),
        get_lead_client=lambda: locator.get("lead_client"),
        get_user_client=lambda: locator.get("user_client"),
        get_source_client=lambda: locator.get("source_client"),
    )


async def create_contact_client() -> ContactClient:
    return ContactClient(
        contact_bitrix_client=await create_contact_bitrix_client(),
        contact_repo=await create_contact_repository(),
    )


async def create_company_bitrix_client() -> CompanyBitrixClient:
    return CompanyBitrixClient(await create_bitrix_client())


async def create_company_repository() -> CompanyRepository:
    locator = ServiceLocator()
    return CompanyRepository(
        session=get_session_context(),
        get_contact_client=lambda: locator.get("contact_client"),
        get_lead_client=lambda: locator.get("lead_client"),
        get_user_client=lambda: locator.get("user_client"),
        get_source_client=lambda: locator.get("source_client"),
    )


async def create_company_client() -> CompanyClient:
    return CompanyClient(
        company_bitrix_client=await create_company_bitrix_client(),
        company_repo=await create_company_repository(),
    )


async def create_billing_repository() -> BillingRepository:
    return BillingRepository(session=get_session_context())


async def create_timeline_comment_bitrix_client() -> (
    TimeLineCommentBitrixClient
):
    return TimeLineCommentBitrixClient(await create_bitrix_client())


async def create_timeline_comment_repository() -> TimelineCommentRepository:
    locator = ServiceLocator()
    return TimelineCommentRepository(
        session=get_session_context(),
        get_user_client=lambda: locator.get("user_client"),
    )


async def create_product_bitrix_client() -> ProductBitrixClient:
    return ProductBitrixClient(await create_bitrix_client())


async def get_service(service_name: str) -> Any:
    """Получает сервис из реестра или создает новый"""
    cache = _services_cache_ctx.get()
    if service_name in cache:
        return cache[service_name]

    # Защита от рекурсии: помечаем сервис как создаваемый
    cache[service_name] = "CREATING"
    _services_cache_ctx.set(cache)

    factory_name = f"create_{service_name}"
    factory = globals().get(factory_name)
    if not factory or not callable(factory):
        raise ValueError(f"Factory for service {service_name} not found")
    # Вызываем фабрику и обрабатываем результат
    result = factory()

    # Если фабрика возвращает корутину - ждем её выполнения
    if inspect.isawaitable(result):
        instance = await result
    else:
        instance = result

    cache[service_name] = instance
    _services_cache_ctx.set(cache)

    return instance


# Dependency для установки контекста запроса
async def request_context(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[None, None]:
    """Устанавливает контекст для текущего запроса"""
    # Устанавливаем сессию и кеш сервисов
    session_token = _session_ctx.set(session)
    cache_token = _services_cache_ctx.set({})
    exists_cache_token = _exists_cache_ctx.set({})
    try:
        yield
    finally:
        # Очищаем кеш и сбрасываем контекст после завершения запроса
        _exists_cache_ctx.reset(exists_cache_token)
        _services_cache_ctx.reset(cache_token)
        _session_ctx.reset(session_token)


# FastAPI Dependency для получения сервисов
async def get_service_dependency(
    service_name: str,
) -> Callable[[], Coroutine[Any, Any, Any]]:
    """Возвращает зависимость для получения сервиса"""

    async def _get_service() -> Any:
        return await get_service(service_name)

    return _get_service


# Явные зависимости для использования в роутерах
async def get_department_client_dep() -> DepartmentClient:
    client = await get_service("department_client")
    return cast(DepartmentClient, client)


async def get_source_client_dep() -> SourceClient:
    client = await get_service("source_client")
    return cast(SourceClient, client)


async def get_user_client_dep() -> UserClient:
    client = await get_service("user_client")
    return cast(UserClient, client)


async def get_contact_client_dep() -> ContactClient:
    client = await get_service("contact_client")
    return cast(ContactClient, client)


async def get_company_client_dep() -> CompanyClient:
    client = await get_service("company_client")
    return cast(CompanyClient, client)


async def get_lead_client_dep() -> LeadClient:
    client = await get_service("lead_client")
    return cast(LeadClient, client)


async def get_deal_client_dep() -> DealClient:
    client = await get_service("deal_client")
    return cast(DealClient, client)


async def get_invoice_client_dep() -> InvoiceClient:
    client = await get_service("invoice_client")
    return cast(InvoiceClient, client)


async def get_deal_bitrix_client_dep() -> DealClient:
    client = await get_service("deal_bitrix_client")
    return cast(DealClient, client)


async def get_invoice_bitrix_client_dep() -> InvoiceBitrixClient:
    client = await get_service("invoice_bitrix_client")
    return cast(InvoiceBitrixClient, client)


async def get_billing_repository_dep() -> BillingRepository:
    client = await get_service("billing_repository")
    return cast(BillingRepository, client)


async def get_delivery_note_repository_dep() -> DeliveryNoteRepository:
    client = await get_service("delivery_note_repository")
    return cast(DeliveryNoteRepository, client)


async def get_timeline_comment_bitrix_client_dep() -> (
    TimeLineCommentBitrixClient
):
    client = await get_service("timeline_comment_bitrix_client")
    return cast(TimeLineCommentBitrixClient, client)


async def get_timeline_comment_repository_dep() -> TimelineCommentRepository:
    client = await get_service("timeline_comment_repository")
    return cast(TimelineCommentRepository, client)


async def get_product_bitrix_client_dep() -> ProductBitrixClient:
    client = await get_service("product_bitrix_client")
    return cast(ProductBitrixClient, client)


async def get_oauth_client() -> BitrixOAuthClient:
    return await create_oauth_client()


def get_exists_cache() -> (
    dict[tuple[Type[Any], tuple[tuple[str, Any], ...]], bool]
):
    """Возвращает кэш проверок существования объектов"""
    return _exists_cache_ctx.get()


def reset_exists_cache() -> None:
    """Сбрасывает кэш проверок"""
    _exists_cache_ctx.set({})


def get_updated_cache() -> set[tuple[Type[Any], int | str]]:
    """Возвращает кэш проверок обновлённых объектов"""
    return _updated_cache_ctx.get()


def reset_updated_cache() -> None:
    """Сбрасывает кэш обновлённых объектов"""
    _updated_cache_ctx.set(set())


def get_creation_cache() -> dict[tuple[Type[Any], int | str], bool]:
    """
    Возвращает кэш для отслеживания создания сущностей в текущем контексте
    """
    return _creation_cache_ctx.get()


def reset_creation_cache() -> None:
    """
    Сбрасывает кэш для отслеживания создания сущностей в текущем контексте
    """
    _creation_cache_ctx.set({})


def get_update_needed_cache() -> set[tuple[Type[Any], int | str]]:
    """
    Возвращает кэш для отслеживания сущностей, требующих обновления
    """
    return _update_needed_cache_ctx.get()


def reset_update_needed_cache() -> None:
    """
    Сбрасывает кэш для отслеживания сущностей, требующих обновления
    """
    _update_needed_cache_ctx.set(set())


def reset_cache() -> None:
    """
    Сбрасывает кэш
    """
    _update_needed_cache_ctx.set(set())
    _creation_cache_ctx.set({})
    _updated_cache_ctx.set(set())
    _exists_cache_ctx.set({})
