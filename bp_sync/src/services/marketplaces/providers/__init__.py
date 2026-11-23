"""Реестр провайдеров маркетплейсов."""

from models.enums import MarketplaceEnum

from .base import AbstractMarketplaceProvider
from .ozon import OzonProvider

_PROVIDERS: dict[MarketplaceEnum, type[AbstractMarketplaceProvider]] = {
    MarketplaceEnum.OZON: OzonProvider,
}


def get_provider(
    marketplace: MarketplaceEnum,
) -> AbstractMarketplaceProvider:
    """Возвращает экземпляр провайдера для указанного маркетплейса."""
    provider_class = _PROVIDERS.get(marketplace)
    if provider_class is None:
        raise ValueError(f"Провайдер для {marketplace.value} не найден")
    return provider_class()
