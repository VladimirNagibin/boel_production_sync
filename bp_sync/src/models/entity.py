from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base


class TypeDeal(Base):
    """
    1 - Продажа BOEL
    3 - Продажа Колонны
    5 - Интернет продажа
    4 - BOEL Engineering
    SALE - Гарантийное обслуживание
    6 - Сервис
    7 - ВЭД
    UC_76MJ0I - Входящие
    UC_FSOZEI - Исходящие
    """

    type_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="type_deal"
    )


class Stage(Base):
    """
    NEW - Не разобрано
    PREPAYMENT_INVOICE - Выявление потребности
    PREPARATION - Заинтересован
    EXECUTING - Согласование условий договор
    FINAL_INVOICE - Выставление счёта
    1 - На отгрузку
    WON - Выиграна
    LOSE - Проиграна
    APOLOGY - Анализ проигрыша
    """

    stage_id: Mapped[str] = mapped_column(unique=True)
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="stage")


class Deal(Base):
    deal_id: Mapped[int] = mapped_column(unique=True)  # ID
    title: Mapped[str]  # TITLE
    type_id: Mapped[str] = mapped_column(
        ForeignKey("typedeals.type_id")
    )  # TYPE_ID
    type_deal: Mapped["TypeDeal"] = relationship(
        "TypeDeal", back_populates="deals"
    )
    stage_id: Mapped[str] = mapped_column(
        ForeignKey("stages.stage_id")
    )  # STAGE_ID
    stage: Mapped["Stage"] = relationship("Stage", back_populates="deals")
