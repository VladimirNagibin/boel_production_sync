from datetime import datetime
from enum import StrEnum
from typing import ClassVar

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from .base_schemas import CommonFieldMixin, EntityAwareSchema
from .fields import FIELDS_PRODUCT


class EntityTypeAbbr(StrEnum):
    CONTACT = "C"
    COMPANY = "CO"
    LEAD = "L"
    DEAL = "D"
    INVOICE = "SI"
    QUOTE = "Q"
    REQUISITE = "RQ"
    ORDER = "O"


class BaseProductEntity(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_PRODUCT

    # Идентификаторы и основные данные
    product_name: str | None = Field(None, alias="productName")  # Название тов
    price: float | None = Field(None, alias="price")  # Цена
    price_exclusive: float | None = Field(
        None, alias="priceExclusive"
    )  # Цена без налога со скидкой
    price_netto: float | None = Field(None, alias="priceNetto")  # PRICE_NETTO
    price_brutto: float | None = Field(
        None, alias="priceBrutto"
    )  # PRICE_BRUTTO
    quantity: float | None = Field(None, alias="quantity")  # Количество
    discount_type_id: int | None = Field(
        None, alias="discountTypeId"
    )  # Тип скидки
    discount_rate: float | None = Field(
        None, alias="discountRate"
    )  # Величина скидки
    discount_sum: float | None = Field(
        None, alias="discountSum"
    )  # Сумма скидки
    tax_rate: float | None = Field(None, alias="taxRate")  # Налог
    tax_included: bool | None = Field(
        None, alias="taxIncluded"
    )  # Налог включен в цену Y/N
    customized: bool | None = Field(None, alias="customized")  # Изменен
    measure_code: int | None = Field(
        None, alias="measureCode"
    )  # Код единицы измерения
    measure_name: str | None = Field(
        None, alias="measureName"
    )  # Единица измерения
    sort: int | None = Field(None, alias="sort")  # Сортировка
    type: int | None = Field(None, alias="type")  # TYPE
    store_id: int | None = Field(None, alias="storeId")  # STORE_ID

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    def equals_ignore_owner(self, other: "BaseProductEntity") -> bool:
        """Сравнивает два объекта, игнорируя поля"""
        fields_meta = self.__class__.model_fields

        for field_name in fields_meta:
            if field_name in [
                "owner_id",
                "owner_type",
                "external_id",
                "sort",
                "store_id",
                "internal_id",
                "created_at",
                "updated_at",
                "is_deleted_in_bitrix",
                "type",
            ]:
                continue

            value1 = getattr(self, field_name)
            value2 = getattr(other, field_name)
            # Специальная обработка для float
            if isinstance(value1, float) and isinstance(value2, float):
                if abs(value1 - value2) > 1e-6:
                    return False
            elif value1 != value2:
                return False

        return True


class ProductEntityCreate(BaseProductEntity, EntityAwareSchema):
    """Модель для создания товаров в сущности"""

    owner_id: int = Field(..., alias="ownerId")  # ID владельца
    owner_type: EntityTypeAbbr = Field(..., alias="ownerType")  # Тип владельца
    product_id: int = Field(..., alias="productId")  # Товар


class ProductEntityUpdate(BaseProductEntity):
    """Модель для частичного обновления товаров в сущности"""

    owner_id: int | None = Field(None, alias="ownerId")  # ID владельца
    owner_type: EntityTypeAbbr | None = Field(
        None, alias="ownerType"
    )  # Тип владельца
    product_id: int | None = Field(None, alias="productId")  # Товар


class ListProductEntity(BaseModel):  # type: ignore[misc]
    """Схема для списка товаров сущности"""

    result: list[ProductEntityCreate]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )

    def equals_ignore_owner(self, other: "ListProductEntity") -> bool:
        """Сравнивает два списка продуктов, игнорируя owner-поля"""
        if len(self.result) != len(other.result):
            return False

        return all(
            item1.equals_ignore_owner(item2)
            for item1, item2 in zip(self.result, other.result)
        )


class BaseProduct(CommonFieldMixin):
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    FIELDS_BY_TYPE: ClassVar[dict[str, str]] = FIELDS_PRODUCT

    code: str | None = Field(
        None, validation_alias=AliasChoices("CODE", "code")
    )  # CODE
    active: bool | None = Field(
        None, validation_alias=AliasChoices("ACTIVE", "active")
    )  # Активен
    sort: int | None = Field(
        None,
        validation_alias=AliasChoices("SORT", "sort"),
    )  # Сортировка
    xml_id: str | None = Field(
        None, validation_alias=AliasChoices("XML_ID", "xmlId")
    )  # Внешний код
    date_create: datetime | None = Field(
        None,
        validation_alias=AliasChoices("DATE_CREATE", "dateCreate"),
    )  # Дата создания
    date_modify: datetime | None = Field(
        None,
        validation_alias=AliasChoices("TIMESTAMP_X", "TIMESTAMP_X"),
    )  # Дата изменения
    modified_by: int | None = Field(
        None,
        validation_alias=AliasChoices("MODIFIED_BY", "modifiedBy"),
    )  # Кем изменён
    created_by: int | None = Field(
        None,
        validation_alias=AliasChoices("CREATED_BY", "createdBy"),
    )  # Кем создан
    catalog_id: int | None = Field(
        None,
        validation_alias=AliasChoices("CATALOG_ID", "iblockId"),
    )  # Каталог
    section_id: int | None = Field(
        None,
        validation_alias=AliasChoices("SECTION_ID", "iblockSectionId"),
    )  # Раздел
    price: float | None = Field(
        None,
        validation_alias=AliasChoices("PRICE", "price"),
    )  # Цена (в каталоге отдельный справочник)
    currency_id: str | None = Field(
        None,
        validation_alias=AliasChoices("CURRENCY_ID", "currency_id"),
    )  # Валюта (в каталоге отдельный справочник)
    vat_id: int | None = Field(
        None,
        validation_alias=AliasChoices("VAT_ID", "vatId"),
    )  # Ставка НДС
    vat_included: bool | None = Field(
        None,
        validation_alias=AliasChoices("VAT_INCLUDED", "vatIncluded"),
    )  # НДС включён в цену Y/N
    measure: int | None = Field(
        None,
        validation_alias=AliasChoices("MEASURE", "measure"),
    )  # Единица измерения
    article: str | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_109", "property109"),
    )  # Артикул
    remains_spb: int | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_113", "property113"),
    )  # Остаток СПб
    remains_kdr: int | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_115", "property115"),
    )  # Остаток Кдр
    remains_msk: int | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_117", "property117"),
    )  # Остаток Мск
    remains_nsk: int | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_119", "property119"),
    )  # Остаток Нск
    price_distributor: float | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_121", "property121"),
    )  # Цена Дистр
    price_minimal: float | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_123", "property123"),
    )  # Цена Мин
    manufacturer: str | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_127", "property127"),
    )  # Производитель
    country: str | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_129", "property129"),
    )  # Страна
    brand: str | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_131", "property131"),
    )  # Бренд
    incentive_tier: int | None = Field(
        None,
        validation_alias=AliasChoices("PROPERTY_151", "property151"),
    )  # Группы товара для мотивации продаж
    # 75:A, 77:B, 79:C, 81:Товар месяца, 83:Не товар, 85:Искл


class ProductCreate(BaseProduct, EntityAwareSchema):
    """Модель для создания товаров"""

    name: str = Field(
        ..., validation_alias=AliasChoices("NAME", "name")
    )  # Название


class ProductUpdate(BaseProduct):
    """Модель для частичного обновления товаров"""

    name: str | None = Field(
        None, validation_alias=AliasChoices("NAME", "name")
    )  # Название


class ListProduct(BaseModel):  # type: ignore[misc]
    """Схема для списка товаров сущности"""

    result: list[ProductCreate]

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )
