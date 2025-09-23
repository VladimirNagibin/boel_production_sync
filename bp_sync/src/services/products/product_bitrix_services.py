from enum import IntEnum
from typing import Any, cast

from fastapi import status

from core.logger import logger
from schemas.product_schemas import (
    EntityTypeAbbr,
    ListProductEntity,
    ProductCreate,
    ProductEntityCreate,
    ProductUpdate,
)

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from ..bitrix_services.bitrix_api_client import BitrixAPIClient
from ..decorators import handle_bitrix_errors
from ..entities.measure_repository import MeasureRepository
from ..exceptions import BitrixApiError
from .code_services import CodeService
from .helper import product_variant_mapping


class CatalogType(IntEnum):
    PRODUCT = 25
    VARIATION = 27
    SITE = 41


PRODUCT_CATALOG = 25
PRODUCT_VARIATION = 27
SITE_CATALOG = 41
DELIVERY_ID = 1845
DELIVERY_NAME = "Организация доставки (экспедирования)"
DELIVERY_MEASURE_CODE = 9
DELIVERY_XML_ID = "00-00000547"
DELIVERY_BOELSHOP = "1#ORDER_DELIVERY"


class ProductBitrixClient(
    BaseBitrixEntityClient[ProductCreate, ProductUpdate]
):
    entity_name = "catalog.product"
    create_schema = ProductCreate
    update_schema = ProductUpdate

    def __init__(
        self,
        bitrix_client: BitrixAPIClient,
        code_service: CodeService,
        measure_repository: MeasureRepository,
    ):
        super().__init__(bitrix_client)
        self.code_service = code_service
        self.measure_repository = measure_repository

    @handle_bitrix_errors()
    async def _get_entity_products(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr,
    ) -> ListProductEntity:
        """Получение товаров в сущности по ID"""
        logger.debug(
            f"Fetching products of owner type:{owner_type} ID={owner_id}"
        )
        params: dict[str, Any] = {
            "filter": {
                "=ownerType": owner_type.value,
                "=ownerId": owner_id,
            }
        }
        response = await self.bitrix_client.call_api(
            "crm.item.productrow.list",
            params=params,
        )
        if (
            not (entity_data := response.get("result"))
            or "productRows" not in entity_data
        ):
            logger.warning(
                f"Products not found for {owner_type} ID={owner_id}"
            )
            return ListProductEntity(result=[])
        return ListProductEntity(result=entity_data["productRows"])

    async def _get_product_catalog(self, product_id: int) -> ProductCreate:
        """Получение каталога товара"""
        return await self.get(entity_id=product_id, crm=False)

    async def _update_product_measure(
        self, product_entity: ProductEntityCreate, measure_id: int
    ) -> bool:
        """Обновление меры измерения продукта"""
        try:
            measure = await self.measure_repository.get_entity(measure_id)
            if measure:
                product_entity.measure_code = measure.measure_code
                product_entity.measure_name = measure.name
                return True
        except Exception:
            logger.warning(f"Couldn't get measure for ID: {measure_id}")
        return False

    async def _update_product_from_conversion(
        self,
        product_entity: ProductEntityCreate,
        product_convert: ProductUpdate,
    ) -> bool:
        """Обновляет сущность продукта на основе преобразованного продукта"""
        if not product_convert:
            return False

        if not isinstance(product_convert.external_id, int):
            logger.warning(
                f"Invalid external_id type for product: {product_convert}"
            )
            return False

        product_entity.product_id = product_convert.external_id
        product_entity.product_name = product_convert.name

        if product_convert.measure:
            return await self._update_product_measure(
                product_entity, product_convert.measure
            )
        return False

    async def _handle_catalog_variation(
        self, product_entity: ProductEntityCreate, xml_id: str | None
    ) -> tuple[bool, str | None]:
        """Обработка товаров из каталога торговых предложений"""
        if not xml_id:
            logger.warning(
                f"xml_id is None for product {product_entity.product_id}"
            )
            return False, None

        product_convert = await self._convert_to_base_product(xml_id)
        if not product_convert:
            return False, None

        update_success = await self._update_product_from_conversion(
            product_entity, product_convert
        )
        return update_success, product_convert.xml_id

    async def _handle_catalog_site(
        self, product_entity: ProductEntityCreate, xml_id: str | None
    ) -> tuple[bool, str | None]:
        """Обработка товаров из каталога BOELSHOP.ru"""
        if not xml_id:
            logger.warning(
                f"xml_id is None for product {product_entity.product_id}"
            )
            return False, None

        # Обработка доставки
        if xml_id == DELIVERY_BOELSHOP:
            product_entity.product_id = DELIVERY_ID
            product_entity.product_name = DELIVERY_NAME
            product_entity.measure_code = DELIVERY_MEASURE_CODE
            return True, DELIVERY_XML_ID

        # Проверка формата xml_id
        if not xml_id.startswith("1#"):
            return False, None

        ext_code = xml_id[2:].strip()

        if "#" in ext_code:  # торговое предложение
            product_convert = await self._convert_to_base_product(ext_code)
        else:  # товарный каталог
            product_convert = await self._get_product_by_xml_id(ext_code)

        if not product_convert:
            return False, None

        update_success = await self._update_product_from_conversion(
            product_entity, product_convert
        )
        return update_success, product_convert.xml_id

    async def _process_catalog_product(
        self,
        product_entity: ProductEntityCreate,
        product_catalog: ProductCreate,
        products: ListProductEntity,
    ) -> bool:
        """Обработка товара из основного каталога"""
        if not self.code_service.is_valid_code(product_catalog.xml_id):
            products.result.remove(product_entity)
            return True
        return False

    async def _process_variation_product(
        self,
        product_entity: ProductEntityCreate,
        product_catalog: ProductCreate,
        products: ListProductEntity,
    ) -> bool:
        """Обработка товара-вариации"""
        res_upd, xml_upd = await self._handle_catalog_variation(
            product_entity, product_catalog.xml_id
        )

        if not res_upd or not self.code_service.is_valid_code(xml_upd):
            products.result.remove(product_entity)
            return True
        return True

    async def _process_site_product(
        self,
        product_entity: ProductEntityCreate,
        product_catalog: ProductCreate,
        products: ListProductEntity,
    ) -> bool:
        """Обработка товара из сайт-каталога"""
        res_upd, xml_upd = await self._handle_catalog_site(
            product_entity, product_catalog.xml_id
        )

        if not res_upd or not self.code_service.is_valid_code(xml_upd):
            products.result.remove(product_entity)
            return True
        return True

    async def _process_product_entity(
        self, product_entity: ProductEntityCreate, products: ListProductEntity
    ) -> bool:
        """Обработка отдельного продукта и возврат флага обновления"""
        try:
            product_catalog = await self._get_product_catalog(
                product_entity.product_id
            )
        except BitrixApiError as e:
            if e.is_bitrix_error("product does not exist."):
                products.result.remove(product_entity)
                return True
            return False
        if product_catalog.catalog_id is None:
            products.result.remove(product_entity)
            return True
        try:
            catalog_type = CatalogType(product_catalog.catalog_id)
        except ValueError:
            products.result.remove(product_entity)
            return True
        handlers = {
            CatalogType.PRODUCT: self._process_catalog_product,
            CatalogType.VARIATION: self._process_variation_product,
            CatalogType.SITE: self._process_site_product,
        }

        if handler := handlers.get(catalog_type):
            return await handler(product_entity, product_catalog, products)
        else:
            products.result.remove(product_entity)
            return True

    @handle_bitrix_errors()
    async def _check_products_entity(
        self, owner_id: int, owner_type: EntityTypeAbbr
    ) -> tuple[ListProductEntity, bool]:
        """
        Проверка товаров в сущности
        Возврат обновлённого списка товаров и флага изменения списка
        """
        products = await self._get_entity_products(owner_id, owner_type)
        update_flag = False
        products_to_process = products.result.copy()

        for product_entity in products_to_process:
            product_update_flag = await self._process_product_entity(
                product_entity, products
            )
            update_flag = update_flag or product_update_flag

        return products, update_flag

    async def _get_product_by_xml_id(
        self, xml_id: str | None
    ) -> ProductUpdate | None:
        """Получение продукта по XML_ID"""
        if not xml_id:
            return None
        products = await self.list(
            filter_entity={"xmlId": xml_id, "iblockId": CatalogType.PRODUCT},
            select=["id", "iblockId", "measure", "name", "xmlId"],
            crm=False,
        )
        return (
            cast(ProductUpdate, products.result[0])
            if products.result
            else None
        )

    async def _convert_to_base_product(
        self, variant_code: str
    ) -> ProductUpdate | None:
        """Преобразует вариант товара в базовый товар"""
        xml_id = product_variant_mapping.get(variant_code)
        return await self._get_product_by_xml_id(xml_id)

    @handle_bitrix_errors()
    async def _set_product_rows(
        self,
        owner_id: int,
        owner_type: EntityTypeAbbr,
        products: ListProductEntity,
    ) -> ListProductEntity:
        """
        Устанавливает товарные позиции в сущность CRM.
        Перезаписывает все существующие товарные позиции.

        Args:
            owner_id: Идентификатор объекта CRM
            owner_type: Краткий символьный код типа объекта CRM
            products: Список товарных позиций для установки

        Returns:
            Ответ от Bitrix24 API
        """
        logger.debug(f"Setting products of {owner_type} ID={owner_id}")
        # Формируем параметры запроса
        params: dict[str, Any] = {
            "ownerId": owner_id,
            "ownerType": owner_type.value,
            "productRows": products.to_bitrix_dict(),
        }
        response = await self.bitrix_client.call_api(
            "crm.item.productrow.set", params=params
        )

        # Проверяем ответ
        if (
            not (entity_data := response.get("result"))
            or "productRows" not in entity_data
        ):
            logger.error(
                f"Failed to set product rows for owner type:{owner_type} "
                f"ID={owner_id}"
            )
            raise BitrixApiError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_description=(
                    f"Failed to set product rows for owner type:{owner_type} "
                    f"ID={owner_id}"
                ),
            )
        return ListProductEntity(result=entity_data["productRows"])

    async def check_update_products_entity(
        self, owner_id: int, owner_type: EntityTypeAbbr
    ) -> ListProductEntity | None:
        """
        Проверяет и обновляет продукты сущности при необходимости.

        Args:
            owner_id: ID сущности-владельца
            owner_type: Тип сущности-владельца

        Returns:
            Кортеж (успех_операции, данные_продуктов)
        """
        try:
            products, needs_update = await self._check_products_entity(
                owner_id, owner_type
            )
            if not needs_update:
                logger.info(
                    f"No product update needed for {owner_type.value} "
                    f"{owner_id}"
                )
                return products
            products_upd = await self._set_product_rows(
                owner_id, owner_type, products
            )
            logger.info(
                f"Successfully updated products for {owner_type.value} "
                f"{owner_id}"
            )
            return products_upd

        except Exception as e:
            logger.error(
                f"Error updating products for {owner_type.value} {owner_id}: "
                f"{str(e)}"
            )
            return None

    async def update_deal_product_from_invoice(
        self, deal_id: int, invoice_id: int
    ) -> bool:
        """
        Проверяет и обновляет товары в сделке из счёта.

        Args:
            deal_id: ID сделки
            invoice_id: ID счёта

        Returns:
            bool
        """
        try:
            deal_products = await self._get_entity_products(
                deal_id, EntityTypeAbbr.DEAL
            )
            invoice_products = await self._get_entity_products(
                invoice_id, EntityTypeAbbr.INVOICE
            )
            if not deal_products.equals_ignore_owner(invoice_products):
                logger.info(
                    f"Products not equals deal:{deal_id}, invoice:{invoice_id}"
                )
                await self._set_product_rows(
                    deal_id, EntityTypeAbbr.DEAL, invoice_products
                )
            logger.info(
                f"Successfully updated products for deal:{deal_id} "
                f"from invoice:{invoice_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error updating products deal:{deal_id}, "
                f"invoice:{invoice_id}. Error: {str(e)}"
            )
            return False
