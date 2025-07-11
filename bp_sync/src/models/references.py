from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import EntityType, NameIntIdEntity, NameStrIdEntity

if TYPE_CHECKING:
    from .company_models import Company
    from .contact_models import Contact
    from .deal_documents import Contract
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
    deal: lead: contact: company
    147: 45: 75: 93: Дистрибьютор
    149: 47: 77: 95: Домашний пивовар
    151: 49: 79: 97: Завод
    153: 51: 81: 99: Крафт
    155: 53: 83: 101: Наш дилер
    157: 55: 85: 103: Розница
    159: 57: 87: 105: Сети
    161: 59: 89: 107: Торговая компания
    163: 61: 91: 109: Хорека
    """

    __tablename__ = "main_activites"
    ext_alt_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с лидом"
    )
    ext_alt2_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с контактом"
    )
    ext_alt3_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с компанией"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="main_activity"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="main_activity"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="main_activity"
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
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="deal_type"
    )


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
    439: 8923: Системы
    441: 5385: Элемент
    443: 5383: Торговый дом СР
    445: 5381: ТехТорг
    447: 22145: ИП Гузиков М.Г.
    773: 23217: ИП Воробьев Д.В.
    777: 8897: Эксперты розлива
    """

    __tablename__ = "shipping_companies"
    ext_alt_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с компанией"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="shipping_company"
    )
    contracts: Mapped[list["Contract"]] = relationship(
        "Contract", back_populates="shipping_company"
    )
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="shipping_company"
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
    deal:lead:contact:company
    685:665:715:735: Нецелевой
    687:667:717:737: Не проходим по ценам
    689:669:719:739: Нет в наличии
    691:671:721:741: Клиент не отвечает
    693:673:723:743: Другое
    """

    __tablename__ = "deal_failure_reasons"
    ext_alt_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с лидом"
    )
    ext_alt2_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с контактом"
    )
    ext_alt3_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи с компанией"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="deal_failure_reason"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="deal_failure_reason"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="deal_failure_reason"
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


class ContactType(NameStrIdEntity):
    """
    Типы сделок:
    CLIENT: Клиенты(Contact)
    CUSTOMER: Клиент(Company)
    COMPETITOR: Конкурент(Company)
    SUPPLIER: Поставщики
    PARTNER: Партнёры
    OTHER: Другое
    1: Не целевой(Contact)
    """

    __tablename__ = "contact_types"
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="type"
    )
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="company_type"
    )


class AdditionalResponsible:
    __tablename__ = "additional_responsibles"
    entity_type: Mapped[EntityType] = mapped_column(
        String(20),
        comment="Тип сущности",
        index=True,
    )  # contact, company
    entity_id: Mapped[int] = mapped_column(
        comment="Внешний ID соответствующей сущности"
    )  # Внешний ID соответствующей сущности
    responsible_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID дополнительного ответственного",
    )


class Industry(NameStrIdEntity):
    """
    Сфера деятельности:
    IT:	Информационные технологии
    TELECOM: Телекоммуникации и связь
    MANUFACTURING: Производство
    BANKING: Банковские услуги
    CONSULTING: Консалтинг
    FINANCE: Финансы
    GOVERNMENT: Правительство
    DELIVERY: Доставка
    ENTERTAINMENT: Развлечения
    NOTPROFIT: Не для получения прибыли
    OTHER: Другое
    1: Торговля
    """

    __tablename__ = "industries"
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="industry"
    )


class Emploees(NameStrIdEntity):
    """
    Сфера деятельности:
    EMPLOYEES_1: менее 50
    EMPLOYEES_2: 50-250
    EMPLOYEES_3: 250-500
    EMPLOYEES_4: более 500
    """

    __tablename__ = "employees"
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="employees"
    )
