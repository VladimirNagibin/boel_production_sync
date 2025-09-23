from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import EntityType, NameIntIdEntity, NameStrIdEntity

if TYPE_CHECKING:
    from .company_models import Company
    from .contact_models import Contact
    from .deal_documents import Contract
    from .deal_models import Deal
    from .delivery_note_models import DeliveryNote
    from .invoice_models import Invoice
    from .lead_models import Lead
    from .user_models import User


CURRENCY_VALUES = [
    ("Российский рубль", "RUB", 1.0, 1),
    ("Доллар США", "USD", 78.4839, 1),
    ("Евро", "EUR", 89.8380, 1),
    ("Гривна", "UAH", 8.8277, 10),
    ("Белорусский рубль", "BYN", 26.3696, 1),
    ("Тенге", "KZT", 15.1277, 100),
]


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
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="currency"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="currency"
    )


MAIN_ACTIVITY_VALUES = [
    ("Дистрибьютор", 147, 45, 75, 93, 411),
    ("Домашний пивовар", 149, 47, 77, 95, 413),
    ("Завод", 151, 49, 79, 97, 415),
    ("Крафт", 153, 51, 81, 99, 417),
    ("Наш дилер", 155, 53, 83, 101, 419),
    ("Розница", 157, 55, 85, 103, 421),
    ("Сети", 159, 57, 87, 105, 423),
    ("Торговая компания", 161, 59, 89, 107, 425),
    ("Хорека", 163, 61, 91, 109, 427),
]


class MainActivity(NameIntIdEntity):
    """
    Основная деятельность клиента:
    deal: lead: contact: company: invoice
    147: 45: 75: 93: 411: Дистрибьютор
    149: 47: 77: 95: 413: Домашний пивовар
    151: 49: 79: 97: 415: Завод
    153: 51: 81: 99: 417: Крафт
    155: 53: 83: 101: 419: Наш дилер
    157: 55: 85: 103: 421: Розница
    159: 57: 87: 105: 423: Сети
    161: 59: 89: 107: 425: Торговая компания
    163: 61: 91: 109: 427: Хорека
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
    ext_alt4_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи со счётом"
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
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="main_activity"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="main_activity"
    )


DEAL_TYPE_VALUES = [
    ("Прямые продажи", "1"),
    ("Продажа Колонны", "3"),
    ("Интернет продажа", "5"),
    ("Маркетплейс", "4"),
    ("Гарантийное обслуживание", "SALE"),
    ("Сервис", "6"),
    ("ВЭД", "7"),
    ("Входящие", "UC_76MJ0I"),
    ("Исходящие", "UC_FSOZEI"),
]


class DealType(NameStrIdEntity):
    """
    Типы сделок:
    1: Прямые продажи
    3: Продажа Колонны
    5: Интернет продажа
    4: Маркетплейс
    SALE: Гарантийное обслуживание
    6: Сервис
    7: ВЭД
    UC_76MJ0I: Входящие
    UC_FSOZEI: Исходящие
    """

    __tablename__ = "deal_types"
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="type", foreign_keys="[Deal.type_id]"
    )
    lead_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="lead_type", foreign_keys="[Deal.lead_type_id]"
    )
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="type")
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="deal_type"
    )
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="deal_type"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="type"
    )


DEAL_STAGE_VALUES = [
    ("Не разобрано", "NEW", 1),
    ("Выявление потребности", "PREPAYMENT_INVOICE", 2),
    ("Заинтересован", "PREPARATION", 3),
    ("Согласование условий договор", "EXECUTING", 4),
    ("Выставление счёта", "FINAL_INVOICE", 5),
    ("На отгрузку", "1", 6),
    ("Выиграна", "WON", 7),
    ("Проиграна", "LOSE", 8),
    ("Анализ проигрыша", "APOLOGY", 9),
]


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
    sort_order: Mapped[int] = mapped_column(
        unique=True, comment="Порядковый номер стадии"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="stage", foreign_keys="[Deal.stage_id]"
    )
    current_deals: Mapped[list["Deal"]] = relationship(
        "Deal",
        back_populates="current_stage",
        foreign_keys="[Deal.current_stage_id]",
    )


CATEGORY_VALUES = [
    ("общее направление", 0),
    ("сервис", 1),
    ("отгрузка со склада", 2),
]


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


SOURCE_VALUES = [
    ("Существующий клиент", "PARTNER"),
    ("Новый клиент", "19"),
    ("Звонок", "CALL"),
    ("Веб-сайт BOELSHOP", "WEB"),
    ("Заказ BOELSHOP", "21"),
    ("Звонок BOELSHOP", "22"),
    ("CRM-форма", "WEBFORM"),
    ("Выбирай", "20"),
    ("EMAIL", "23"),
    # deprecated
    ("OZON", "16"),
    ("WILDBERRIES", "17"),
    ("ЮЛА", "7"),
    ("АВИТО", "5"),
    ("Avito - BOEL SHOP AVITO", "9|AVITO"),
    ("Интернет-магазин", "STORE"),
    ("Другое", "UC_7VUX6L"),
    ("ВКонтакте - Открытая линия", "1|VK"),
    ("Обратный звонок", "CALLBACK"),
    ("Алиэкспресс", "12"),
    ("Генератор продаж", "RC_GENERATOR"),
    ("Шоп и периферия", "UC_2THEVX"),
    ("Повторные продажи", "REPEAT_SALE"),
    ("Существующий клиент", "Существующий клиент"),
    ("OTHER", "OTHER"),
    ("26", "26"),
]


class Source(NameStrIdEntity):
    """
    Источники сделок:
    PARTNER: Существующий клиент
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
    # 20: Выбирай
    # 21: Интернет
    # EMAIL: EMAIL
    # Существующий клиент: Существующий клиент
    # OTHER: OTHER
    # 26: 26
    """

    __tablename__ = "sources"
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="source")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="source")
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="source"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="source"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="source"
    )


CREATION_SOURCE_VALUES = [
    ("авто", 805, 541),
    ("ручной", 807, 541),
    # deprecated
    ("Существующий клиент", 499, 535),
    ("Новый клиент", 501, 537),
    ("Шоурум", 503, 539),
    ("Интернет", 505, 541),
]


class CreationSource(NameIntIdEntity):
    """
    Источники создания сделок:
    deal: invoice
    499: 535: Существующий клиент
    501: 537: Новый клиент
    503: 539: Шоурум
    505: 541: Интернет
    805: 500: авто *500 - test
    807: 502: ручной *502 - test
    """

    __tablename__ = "creation_sources"
    ext_alt_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи со счётом"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="creation_source"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="creation_source"
    )


INVOICE_STAGE_VALUES = [
    ("новый", "DT31_1:N", 1),
    ("отправлен", "DT31_1:S", 2),
    ("успешный", "DT31_1:P", 3),
    ("не оплачен", "DT31_1:D", 4),
]


class InvoiceStage(NameStrIdEntity):
    """
    Стадии счетов:
    1. DT31_1:N: новый
    2. DT31_1:S: отправлен
    # 3. 1: выгружен в 1С
    3. DT31_1:P: успешный
    4. DT31_1:D: не оплачен
    """

    __tablename__ = "invoice_stages"
    sort_order: Mapped[int] = mapped_column(
        unique=True, comment="Порядковый номер"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="invoice_stage"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="invoice_stage",
        foreign_keys="[Invoice.invoice_stage_id]",
    )
    previous_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="previous_stage",
        foreign_keys="[Invoice.previous_stage_id]",
    )
    current_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="current_stage",
        foreign_keys="[Invoice.current_stage_id]",
    )


SHIPPING_COMPANY_VALUES = [
    ("Системы", 8923, 439),
]


class ShippingCompany(NameIntIdEntity):
    """
    Фирмы отгрузки
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
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="shipping_company"
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote", back_populates="shipping_company"
    )


WAREHOUSE_VALUES = [
    ("Нск", 597, 481),
    ("Спб", 599, 483),
    ("Кдр", 601, 485),
    ("Мск", 603, 487),
]


class Warehouse(NameIntIdEntity):
    """
    Склады
    deal: invoice
    597: 481: Нск
    599: 483: Спб
    601: 485: Кдр
    603: 487: Мск
    """

    __tablename__ = "warehouses"
    ext_alt_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи со счётом"
    )
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="warehouse"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="warehouse"
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote", back_populates="warehouse"
    )


DEFECT_TYPE_VALUES = [
    ("Некомплектная поставка", 527),
    ("Некачественная сборка/проверка", 529),
    ("Дефект материала", 553),
    ("Дефект изготовления комплектующих", 555),
    ("Транспортное повреждение", 557),
    ("Негарантийная поломка", 559),
]


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
    # deal_id: Mapped[UUID] = mapped_column(ForeignKey("deals.id"))
    # deal: Mapped["Deal"] = relationship("Deal", back_populates="defects")


DEAL_FAILURE_REASON_VALUES = [
    ("Нецелевой", 685, 665, 715, 735, 763),
    ("Не проходим по ценам", 687, 667, 717, 737, 765),
    ("Нет в наличии", 689, 669, 719, 739, 767),
    ("Клиент не отвечает", 691, 671, 721, 741, 769),
    ("Другое", 693, 673, 723, 743, 771),
]


class DealFailureReason(NameIntIdEntity):
    """
    Причины провала
    deal:lead:contact:company: invoice
    685:665:715:735: 763: Нецелевой
    687:667:717:737: 765: Не проходим по ценам
    689:669:719:739: 767: Нет в наличии
    691:671:721:741: 769: Клиент не отвечает
    693:673:723:743: 771: Другое
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
    ext_alt4_id: Mapped[int] = mapped_column(
        unique=True, comment="id для связи со счётом"
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
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="deal_failure_reason"
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="invoice_failure_reason"
    )


LEAD_STATUS_VALUES = [
    ("Входящий лид", "NEW", 1),
    ("Зависшие лиды", "UC_2N339H", 2),
    ("Идентификация", "1", 3),
    ("Квалификация", "IN_PROCESS", 4),
    ("В разработке", "2", 5),
    ("Качественный лид", "CONVERTED", 6),
    ("Некачественный лид", "JUNK", 7),
]


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
    sort_order: Mapped[int] = mapped_column(
        unique=True, comment="Порядковый номер"
    )
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="status")


CONTACT_TYPE_VALUES = [
    ("Клиенты", "CLIENT"),
    ("Клиент", "CUSTOMER"),
    ("Конкурент", "COMPETITOR"),
    ("Поставщики", "SUPPLIER"),
    ("Партнёры", "PARTNER"),
    ("Другое", "OTHER"),
    ("Не целевой", "1"),
]


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


INDUSTRY_VALUES = [
    ("Информационные технологии", "IT"),
    ("Телекоммуникации и связь", "TELECOM"),
    ("Производство", "MANUFACTURING"),
    ("Банковские услуги", "BANKING"),
    ("Консалтинг", "CONSULTING"),
    ("Финансы", "FINANCE"),
    ("Правительство", "GOVERNMENT"),
    ("Доставка", "DELIVERY"),
    ("Развлечения", "ENTERTAINMENT"),
    ("Не для получения прибыли", "NOTPROFIT"),
    ("Другое", "OTHER"),
    ("Торговля", "1"),
]


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


EMPLORRS_VALUES = [
    ("менее 50", "EMPLOYEES_1"),
    ("50-250", "EMPLOYEES_2"),
    ("250-500", "EMPLOYEES_3"),
    ("более 500", "EMPLOYEES_4"),
]


class Emploees(NameStrIdEntity):
    """
    Количесиво сотрудников:
    EMPLOYEES_1: менее 50
    EMPLOYEES_2: 50-250
    EMPLOYEES_3: 250-500
    EMPLOYEES_4: более 500
    """

    __tablename__ = "employees"
    companies: Mapped[list["Company"]] = relationship(
        "Company", back_populates="employees"
    )


class Department(NameIntIdEntity):
    """
    Отделы:
    (предзаполнить)
    """

    __tablename__ = "departments"
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.external_id"), nullable=True
    )
    child_departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent_department",
        foreign_keys="[Department.parent_id]",
    )
    parent_department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="child_departments",
        foreign_keys="[Department.parent_id]",
        remote_side="[Department.external_id]",
    )
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="department"
    )


MEASURE_VALUES = [
    (1, "м", 6),
    (3, "л.", 112),
    (5, "г", 163),
    (7, "кг", 166),
    (9, "шт", 796),
    (11, "упак", 778),
]


class Measure(NameIntIdEntity):
    """
    Единицы измерения:
    (предзаполнить)
    """

    __tablename__ = "measures"

    measure_code: Mapped[int] = mapped_column(
        comment="Код единицы измерения"
    )  # MEASURE_CODE
