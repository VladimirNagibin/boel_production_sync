from enum import IntEnum, StrEnum


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


class TypePaymentEnum(IntEnum):
    """
    Типы оплат:
    377 - Предоплата
    379 - Отсрочка
    381 - Частичная
    0 - Не определено
    """

    PREPAYMENT = 377
    POSTPONEMENT = 379
    PARTPAYMENT = 381
    NOT_DEFINE = 0


class TypeShipmentEnum(IntEnum):
    """
    Типы отгрузки:
    515 - Самовывоз
    517 - Доставка курьером
    519 - Отправка ТК
    0 - Не определено
    """

    PICKUP = 515
    DELIVERY_COURIER = 517
    TRANSPORT_COMPANY = 519
    NOT_DEFINE = 0


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
