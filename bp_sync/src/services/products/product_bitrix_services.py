from typing import Any

from fastapi import HTTPException, status

from core.logger import logger
from schemas.product_schemas import (  # ListProduct,
    EntityTypeAbbr,
    ListProductEntity,
    ProductCreate,
    ProductEntityCreate,
    ProductUpdate,
)

from ..bitrix_services.base_bitrix_services import BaseBitrixEntityClient
from ..decorators import handle_bitrix_errors
from .helper import product_variant_mapping


class ProductBitrixClient(
    BaseBitrixEntityClient[ProductCreate, ProductUpdate]
):
    entity_name = "catalog.product"
    create_schema = ProductCreate
    update_schema = ProductUpdate

    @handle_bitrix_errors()
    async def get_entity_products(
        self, owner_id: int, owner_type: EntityTypeAbbr
    ) -> ListProductEntity:
        """Получение товаров в сущности по ID"""
        logger.debug(f"Fetching products of {owner_type} ID={owner_id}")
        params: dict[str, Any] = {
            "filter": {
                "=ownerType": owner_type.value,
                "=ownerId": owner_id,
            }
        }
        response = await self.bitrix_client.call_api(
            "crm.item.productrow.list", params=params
        )
        if not (entity_data := response.get("result")) or not (
            products := entity_data.get("productRows")
        ):
            logger.warning(f"{owner_type} products not found: ID={owner_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{owner_type} products not found: ID={owner_id}",
            )
        return ListProductEntity(result=products)

    async def _get_product_catalog(self, product_id: int) -> ProductCreate:
        """
        Вспомогательный метод для получения каталога товара с обработкой ошибок
        """
        try:
            return await self.get(entity_id=product_id, crm=False)
        except Exception as e:
            logger.error(
                f"Product not found: ID={product_id}, error: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: ID={product_id}, error: {str(e)}",
            )

    async def _update_product_from_conversion(
        self,
        product_entity: ProductEntityCreate,
        product_convert: ProductUpdate,
    ) -> None:
        """Обновляет сущность продукта на основе преобразованного продукта"""
        if not product_convert:
            return

        if isinstance(product_convert.external_id, int):
            product_entity.product_id = product_convert.external_id
        else:
            logger.warning(
                f"Invalid external_id type for product: {product_convert}"
            )
        product_entity.product_name = product_convert.name
        product_entity.measure_code = product_convert.measure

    async def _handle_catalog_27(
        self, product_entity: ProductEntityCreate, xml_id: str | None
    ) -> bool:
        """Обработка товаров из каталога 27 (торговые предложения)"""
        if not xml_id:
            logger.warning(
                f"xml_id is None for product {product_entity.product_id}"
            )
            return True

        product_convert = await self.convert_to_base_product(xml_id)
        if product_convert:
            await self._update_product_from_conversion(
                product_entity, product_convert
            )
            return True
        return False

    async def _handle_catalog_41(
        self, product_entity: ProductEntityCreate, xml_id: str | None
    ) -> bool:
        """Обработка товаров из каталога 41 (BOELSHOP.ru)"""
        if xml_id is None:
            logger.warning(
                f"xml_id is None for product {product_entity.product_id}"
            )
            return False
        if xml_id == "1#ORDER_DELIVERY":  # доставка
            product_entity.product_id = 1845
            product_entity.product_name = (
                "Организация доставки (экспедирования)"
            )
            product_entity.measure_code = 9
            return True

        if not xml_id.startswith("1#"):
            return False

        ext_code = xml_id[2:].strip()

        if "#" in ext_code:  # торговое предложение
            product_convert = await self.convert_to_base_product(xml_id)
            if product_convert:
                await self._update_product_from_conversion(
                    product_entity, product_convert
                )
        else:  # товарный каталог
            products = await self.list(
                filter_entity={"xmlId": ext_code, "iblockId": 25},
                select=["id", "iblockId", "measure", "name"],
                crm=False,
            )

            if products.result:
                await self._update_product_from_conversion(
                    product_entity, products.result[0]
                )

        return True

    @handle_bitrix_errors()
    async def check_products_entity(
        self, owner_id: int, owner_type: EntityTypeAbbr
    ) -> tuple[ListProductEntity, bool]:
        """Проверка товаров в сущности"""
        update_flag = False

        try:
            products = await self.get_entity_products(owner_id, owner_type)
        except Exception as e:
            logger.error(
                f"{owner_type} products not found: ID={owner_id}, "
                f"error: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"{owner_type} products not found: ID={owner_id}, "
                    f"error: {str(e)}"
                ),
            )

        for product_entity in products.result:
            product_catalog = await self._get_product_catalog(
                product_entity.product_id
            )
            catalog_id = product_catalog.catalog_id
            xml_id = product_catalog.xml_id

            if catalog_id == 25:  # товарный каталог
                continue  # Ничего не делаем, всё OK

            elif catalog_id == 27:  # торговое предложение
                update_flag = (
                    await self._handle_catalog_27(product_entity, xml_id)
                    or update_flag
                )

            elif catalog_id == 41:  # каталог BOELSHOP.ru
                update_flag = (
                    await self._handle_catalog_41(product_entity, xml_id)
                    or update_flag
                )
            else:
                ...  # не известный каталог
        return products, update_flag

    async def convert_to_base_product(
        self, variant_code: str
    ) -> ProductUpdate | None:
        """Преобразует вариант товара в базовый товар"""
        xml_id = product_variant_mapping.get(variant_code)

        if not xml_id:
            return None

        products = await self.list(
            filter_entity={"xmlId": xml_id, "iblockId": 25},
            select=["id", "iblockId", "measure", "name"],
            crm=False,
        )

        return products.result[0] if products.result else None
