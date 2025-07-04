from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import NameIntIdEntity, NameStrIdEntity

if TYPE_CHECKING:
    from .deal_models import Deal
    from .lead_models import Lead


class Currency(NameStrIdEntity):
    """
    Валюты:
    ID    name              cource~ nominal
    RUB   Российский рубль  1       1
    USD   Доллар США        78.4839 1
    EUR   Евро              89.8380 1
    UAH   Гривна            18.8277 10
    BYN   Белорусский рубль 26,3696 1
    KZT   Тенге             15.1277 100
    """

    __tablename__ = "currencies"
    rate: Mapped[float] = mapped_column(comment="Курс валюты")
    nominal: Mapped[int] = mapped_column(comment="Номинал")
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="currency"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="currency"
    )


class MainActivity(NameIntIdEntity):
    """
    Основная деятельность клиента:
    deal: lead
    147: 45: Дистрибьютор
    149: 47: Домашний пивовар
    151: 49: Завод
    153: 51: Крафт
    155: 53: Наш дилер
    157: 55: Розница
    159: 57: Сети
    161: 59: Торговая компания
    163: 61: Хорека
    """

    __tablename__ = "main_activites"
    ext_alt_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с лидом"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="main_activity"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="main_activity"
    )


class DealType(NameStrIdEntity):
    """
    Типы сделок:
    1: Продажа BOEL
    3: Продажа Колонны
    5: Интернет продажа
    4: BOEL Engineering
    SALE: Гарантийное обслуживание
    6: Сервис
    7: ВЭД
    UC_76MJ0I: Входящие
    UC_FSOZEI: Исходящие
    """

    __tablename__ = "deal_types"
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="type")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="type")


class DealStage(NameStrIdEntity):
    """
    Стадии сделок:
    1. NEW: Не разобрано
    2. PREPAYMENT_INVOICE: Выявление потребности
    3. PREPARATION: Заинтересован
    4. EXECUTING: Согласование условий договор
    5. FINAL_INVOICE: Выставление счёта
    6. 1: На отгрузку
    7. WON: Выиграна
    8. LOSE: Проиграна
    9. APOLOGY: Анализ проигрыша
    """

    __tablename__ = "deal_stages"
    order: Mapped[int] = mapped_column(
        unique=True, comment="Порядковый номер стадии"
    )
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="stage")
    current_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="current_stage"
    )


class Category(NameIntIdEntity):
    """
    Направления сделок (воронки):
    0: общее направление
    1: сервис
    2: отгрузка со склада
    """

    __tablename__ = "categories"
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="category"
    )


class Source(NameStrIdEntity):
    """
    Источники сделок:
    PARTNER:  Существующий клиент
    19: Новый клиент
    CALL: Звонок
    WEB: Веб-сайт BOELSHOP
    16: OZON
    17: WILDBERRIES
    7: ЮЛА
    5: АВИТО
    9|AVITO: Avito - BOEL SHOP AVITO
    STORE: Интернет-магазин
    UC_7VUX6L: Другое
    1|VK: ВКонтакте - Открытая линия
    CALLBACK: Обратный звонок
    WEBFORM: CRM-форма
    12: Алиэкспресс
    RC_GENERATOR: Генератор продаж
    UC_2THEVX: Шоп и периферия
    REPEAT_SALE: Повторные продажи
    # 20: Шоурум
    # 21: Интернет
    """

    __tablename__ = "sources"
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="source")
    leads: Mapped[list["Lead"]] = relationship("lead", back_populates="source")


class CreationSource(NameIntIdEntity):
    """
    Источники создания сделок:
    499: Существующий клиент
    501: Новый клиент
    503: Шоурум
    505: Интернет
    # Ручная / Автоматическая
    """

    __tablename__ = "creation_sources"
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="creation_source"
    )


class InvoiceStage(NameStrIdEntity):
    """
    Стадии счетов:
    1. N: новый
    2. S: отправлен
    3. 1: выгружен в 1С
    4. P: успешный
    5. D: не оплачен
    """

    __tablename__ = "invoice_stages"
    order: Mapped[int] = mapped_column(unique=True, comment="Порядковый номер")
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="invoice_stage"
    )


class ShippingCompany(NameIntIdEntity):
    """
    Фирмы отгрузки
    439: Системы
    441: Элемент
    443: Торговый дом СР
    445: ТехТорг
    447: ИП Гузиков М.Г.
    773: ИП Воробьев Д.В.
    777: Эксперты розлива
    """

    __tablename__ = "shipping_companies"
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="shipping_company"
    )


class Warehouse(NameIntIdEntity):
    """
    Склады
    597: Нск
    599: Спб
    601: Кдр
    603: Мск
    """

    __tablename__ = "warehouses"
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="warehouse"
    )


class DefectType(NameIntIdEntity):
    """
    Виды неисправностей:
    527: Некомплектная поставка
    529: Некачественная сборка/проверка
    553: Дефект материала
    555: Дефект изготовления комплектующих
    557: Транспортное повреждение
    559: Негарантийная поломка
    """

    __tablename__ = "defect_types"
    deal_id: Mapped[UUID] = mapped_column(ForeignKey("deals.id"))
    deal: Mapped["Deal"] = relationship("Deal", back_populates="defects")


class DealFailureReason(NameIntIdEntity):
    """
    Причины провала
    deal:lead
    685:665: Нецелевой
    687:667: Не проходим по ценам
    689:669: Нет в наличии
    691:671: Клиент не отвечает
    693:673: Другое
    """

    __tablename__ = "deal_failure_reasons"
    ext_alt_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с лидом"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="deal_failure_reason"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="deal_failure_reason"
    )


class LeadStatus(NameStrIdEntity):
    """
    Стадии счетов:
    1. NEW: Входящий лид
    2. UC_2N339H: Зависшие лиды
    3. 1: Идентификация
    4. IN_PROCESS: Квалификация
    5. 2: В разработке
    6. CONVERTED: Качественный лид
    7. JUNK: Некачественный лид
    """

    __tablename__ = "lead_statuses"
    order: Mapped[int] = mapped_column(unique=True, comment="Порядковый номер")
    leads: Mapped[list["Deal"]] = relationship(
        "Lead", back_populates="lead_status"
    )
