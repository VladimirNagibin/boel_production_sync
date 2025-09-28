from enum import Enum, IntEnum, StrEnum
from typing import Any

from sqlalchemy import Integer, TypeDecorator
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeEngine


class StageSemanticEnum(StrEnum):
    """
    Статусы стадии сделки:
    P - В работе(processing)
    S - Успешная(success)
    F - Провал(failed)
    """

    PROSPECTIVE = "P"
    SUCCESS = "S"
    FAIL = "F"

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """Get display name by value"""
        display_name_map: dict[str, str] = {
            "P": "В работе",
            "S": "Успех",
            "F": "Провал",
        }
        return display_name_map.get(value, "Неизвестно")


# class TypePaymentEnum(IntEnum):
#    """
#    Типы оплат:
#    377 - Предоплата
#    379 - Отсрочка
#    381 - Частичная
#    0 - Не определено
#    """

#    PREPAYMENT = 377
#    POSTPONEMENT = 379
#    PARTPAYMENT = 381
#    NOT_DEFINE = 0


class DualTypePaymentEnum(Enum):
    """
    Типы оплат:
    deal: invoice:
    377: 493 - Предоплата
    379: 495 - Отсрочка
    381: 497 - Частичная
    0 - Не определено
    """

    PREPAYMENT = (377, 493)
    POSTPONEMENT = (379, 495)
    PARTPAYMENT = (381, 497)
    NOT_DEFINE = (0, 0)

    @property
    def deal_value(self) -> int:
        return self.value[0]

    @property
    def invoice_value(self) -> int:
        return self.value[1]

    @classmethod
    def _missing_(cls, value: object) -> "DualTypePaymentEnum":
        if isinstance(value, int):
            for item in cls:
                if value == item.deal_value or value == item.invoice_value:
                    return item
        return cls.NOT_DEFINE

    @classmethod
    def get_display_name(cls, value: "DualTypePaymentEnum") -> str:
        """Get display name by value"""
        display_name_map: dict[DualTypePaymentEnum, str] = {
            DualTypePaymentEnum.PREPAYMENT: "Предоплата",
            DualTypePaymentEnum.POSTPONEMENT: "Отсрочка",
            DualTypePaymentEnum.PARTPAYMENT: "Частичная",
            DualTypePaymentEnum.NOT_DEFINE: "Не определено",
        }
        return display_name_map.get(value, "Неизвестно")


class DualTypePayment(
    TypeDecorator[DualTypePaymentEnum | None]  # type: ignore[misc]
):
    """Кастомный тип для сохранения разных значений перечисления"""

    impl = Integer  # Базовый тип в базе данных
    cache_ok = True

    def __init__(self, value_type: str, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.value_type = value_type  # 'deals' или 'invoices'

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        """Определяем физический тип данных для разных СУБД"""
        return dialect.type_descriptor(Integer())

    def process_bind_param(
        self, value: DualTypePaymentEnum | None, dialect: Dialect
    ) -> int | None:
        """Преобразует значение Python в значение базы данных"""
        if value is None:
            return None
        if self.value_type == "deals":
            return value.deal_value
        return value.invoice_value

    def process_result_value(
        self, value: int | None, dialect: Dialect
    ) -> DualTypePaymentEnum | None:
        """Преобразует значение базы данных в значение Python"""
        if value is None:
            return None

        # Ищем подходящий элемент перечисления
        for item in DualTypePaymentEnum:
            if self.value_type == "deals" and item.deal_value == value:
                return item
            if self.value_type == "invoices" and item.invoice_value == value:
                return item
        return DualTypePaymentEnum.NOT_DEFINE


# class TypeShipmentEnum(IntEnum):
#    """
#    Типы отгрузки:
#    515 - Самовывоз
#    517 - Доставка курьером
#    519 - Отправка ТК
#    0 - Не определено
#    """

#    PICKUP = 515
#    DELIVERY_COURIER = 517
#    TRANSPORT_COMPANY = 519
#    NOT_DEFINE = 0


class DualTypeShipmentEnum(Enum):
    """
    Типы отгрузки:
    deal: invoice:
    515: 543 - Самовывоз
    517: 545 - Доставка курьером
    519: 547 - Отправка ТК
    0 - Не определено
    """

    PICKUP = (515, 543)
    DELIVERY_COURIER = (517, 545)
    TRANSPORT_COMPANY = (519, 547)
    NOT_DEFINE = (0, 0)

    @property
    def deal_value(self) -> int:
        return self.value[0]

    @property
    def invoice_value(self) -> int:
        return self.value[1]

    @classmethod
    def _missing_(cls, value: object) -> "DualTypeShipmentEnum":
        if isinstance(value, int):
            for item in cls:
                if value == item.deal_value or value == item.invoice_value:
                    return item
        return cls.NOT_DEFINE

    @classmethod
    def get_display_name(cls, value: "DualTypeShipmentEnum") -> str:
        """Get display name by value"""
        display_name_map: dict[DualTypeShipmentEnum, str] = {
            DualTypeShipmentEnum.PICKUP: "Самовывоз",
            DualTypeShipmentEnum.DELIVERY_COURIER: "Доставка курьером",
            DualTypeShipmentEnum.TRANSPORT_COMPANY: "Отправка ТК",
            DualTypeShipmentEnum.NOT_DEFINE: "Не определено",
        }
        return display_name_map.get(value, "Неизвестно")


class DualTypeShipment(
    TypeDecorator[DualTypeShipmentEnum | None]  # type: ignore[misc]
):
    """Кастомный тип для сохранения разных значений перечисления"""

    impl = Integer  # Базовый тип в базе данных
    cache_ok = True

    def __init__(self, value_type: str, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.value_type = value_type  # 'deals' или 'invoices'

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        """Определяем физический тип данных для разных СУБД"""
        return dialect.type_descriptor(Integer())

    def process_bind_param(
        self, value: DualTypeShipmentEnum | None, dialect: Dialect
    ) -> int | None:
        """Преобразует значение Python в значение базы данных"""
        if value is None:
            return None
        if self.value_type == "deals":
            return value.deal_value
        return value.invoice_value

    def process_result_value(
        self, value: int | None, dialect: Dialect
    ) -> DualTypeShipmentEnum | None:
        """Преобразует значение базы данных в значение Python"""
        if value is None:
            return None

        # Ищем подходящий элемент перечисления
        for item in DualTypeShipmentEnum:
            if self.value_type == "deals" and item.deal_value == value:
                return item
            if self.value_type == "invoices" and item.invoice_value == value:
                return item
        return DualTypeShipmentEnum.NOT_DEFINE


class ProcessingStatusEnum(IntEnum):
    """
    Статусы обработки:
    781 - ОК
    783 - Риск просрочки
    785 - Просрочен
    0 - Не определено
    """

    OK = 781
    AT_RISK = 783
    OVERDUE = 785
    NOT_DEFINE = 0

    @classmethod
    def get_display_name(cls, value: int) -> str:
        """Get display name by value"""
        display_name_map: dict[int, str] = {
            781: "ОК",
            783: "Риск просрочки",
            785: "Просрочен",
            0: "Не определено",
        }
        return display_name_map.get(value, "Неизвестно")


class MethodPaymentEnum(IntEnum):
    """
    форма оплаты:
    489 - Безнал
    491 - Наличные
    493 - Зачёт
    0 - Не определено
    """

    CASH = 489
    CASHLESS = 491
    SETTLEMENT = 493
    NOT_DEFINE = 0


class PaymentTermEnum(IntEnum):
    """
    тип оплаты:
    493 - Предоплата
    495 - Отсрочка
    497 - Частичная
    0 - Не определено
    """

    ADVANCE = 493
    DEFERRED = 495
    PARTIAL = 497
    NOT_DEFINE = 0


# class ShippingMethodEnum(IntEnum):
#    """
#    Способ физической передачи товара покупателю
#    543 - Самовывоз
#    545 - Доставка курьером
#    547 - Отправка ТК
#    """
#    PICKUP = 543
#    COURIER = 545
#    TRANSPORT_COMPANY = 547
#    NOT_DEFINE = 0
