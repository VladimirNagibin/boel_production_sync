from typing import Any

from fastapi import HTTPException, status

from core.logger import logger
from schemas.product_schemas import (  # ListProduct,
    EntityTypeAbbr,
    ListProductEntity,
    ProductCreate,
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
        params: dict[str, Any] = {}
        logger.debug(f"Fetching products of {owner_type} ID={owner_id}")
        params["filter"] = {
            "=ownerType": owner_type.value,
            "=ownerId": owner_id,
        }
        response = await self.bitrix_client.call_api(
            "crm.item.productrow.list", params=params
        )
        if not (entity_data := response.get("result")):
            logger.warning(f"{owner_type} products not found: ID={owner_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{owner_type} products not found: ID={owner_id}",
            )
        if not (products := entity_data.get("productRows")):
            logger.warning(f"{owner_type} products not found: ID={owner_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{owner_type} products not found: ID={owner_id}",
            )
        return ListProductEntity(result=products)

    @handle_bitrix_errors()
    async def check_products_entity(
        self, owner_id: int, owner_type: EntityTypeAbbr
    ) -> tuple[ListProductEntity, bool]:
        """Проверка товаров в сущности"""
        update_flag = False
        try:
            products = await self.get_entity_products(owner_id, owner_type)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"{owner_type} products not found: ID={owner_id}, "
                    f"error: {str(e)}"
                ),
            )
        for product_entity in products.result:
            try:
                product_catalog = await self.get(
                    entity_id=product_entity.product_id, crm=False
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Product not found: ID={product_entity.product_id}, "
                        f"error: {str(e)}"
                    ),
                )
            catalog_id = product_catalog.catalog_id
            xml_id = product_catalog.xml_id
            # measure = product_catalog.measure
            # name = product_catalog.name
            if catalog_id == 25:
                ...  # OK
            elif catalog_id == 27:
                if xml_id is not None:
                    product_convert = await self.convert_to_base_product(
                        xml_id
                    )
                else:
                    product_convert = None
                    logger.warning(
                        "xml_id is None for product "
                        f"{product_entity.product_id}"
                    )
                if product_convert:
                    if product_convert and isinstance(
                        product_convert.external_id, int
                    ):
                        product_entity.product_id = product_convert.external_id
                    else:
                        logger.warning(
                            "Invalid external_id type for product: "
                            f"{product_convert}"
                        )
                        # product_entity.product_id=product_convert.external_id
                    product_entity.product_name = product_convert.name
                    product_entity.measure_code = product_convert.measure
        return products, update_flag

    async def convert_to_base_product(
        self, variant_code: str
    ) -> ProductUpdate | None:
        xml_id = product_variant_mapping.get(variant_code)
        if xml_id:
            products = await self.list(
                filter_entity={"xmlId": xml_id, "iblockId": 25},
                select=["id", "iblockId", "measure", "name"],
                crm=False,
            )
            if result := products.result:
                return result[0]
        return None
