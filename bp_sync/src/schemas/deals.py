from typing import Optional

from pydantic import BaseModel, Field, validator


class DealCreateBase(BaseModel):  # type: ignore[misc]
    """Базовая схема с алиасами для исходных имен полей"""

    ID: int = Field(..., alias="deal_id", description="Уникальный ID сделки")
    TITLE: str = Field(
        ..., alias="title", max_length=255, description="Название сделки"
    )
    TYPE_ID: str = Field(..., alias="type_id", description="ID типа сделки")
    STAGE_ID: str = Field(
        ..., alias="stage_id", description="ID стадии сделки"
    )
    CURRENCY_ID: str = Field(..., alias="currency_id", description="ID валюты")
    OPPORTUNITY: float = Field(
        ..., alias="opportunity", ge=0, description="Сумма сделки (>=0)"
    )
    IS_MANUAL_OPPORTUNITY: bool = Field(
        ...,
        alias="is_manual_opportunity",
        description="Ручное изменение суммы",
    )
    PROBABILITY: Optional[int] = Field(
        None,
        alias="probability",
        ge=0,
        le=100,
        description="Вероятность закрытия (0-100%)",
    )

    @validator("PROBABILITY")  # type: ignore[misc]
    def validate_probability(cls, v: Optional[int]) -> Optional[int]:
        """Кастомная валидация вероятности сделки"""
        if v is not None and (0 <= v <= 100):
            raise ValueError("Probability must be between 0 and 100")
        return v

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
        extra = "forbid"  # Запрещает дополнительные поля


class DealCreate(DealCreateBase):
    """Схема для создания сделки (может включать дополнительные поля/логику)"""

    pass


class DealResponse(BaseModel):  # type: ignore[misc]
    """Схема для ответа API"""

    id: int = Field(..., description="Внутренний ID в базе данных")
    deal_id: int = Field(..., description="Уникальный ID сделки")
    title: str = Field(..., description="Название сделки")
    type_id: str = Field(..., description="ID типа сделки")
    stage_id: str = Field(..., description="ID стадии сделки")
    currency_id: str = Field(..., description="ID валюты")
    opportunity: float = Field(..., description="Сумма сделки")
    is_manual_opportunity: bool = Field(
        ..., description="Ручное изменение суммы"
    )
    probability: Optional[int] = Field(
        None, description="Вероятность закрытия"
    )

    class Config:
        orm_mode = True  # Для автоматической конвертации ORM-объектов


class DealListResponse(BaseModel):  # type: ignore[misc]
    """Схема для ответа со списком сделок"""

    items: list[DealResponse]
    count: int
