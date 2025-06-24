import uuid
from datetime import datetime
from enum import IntEnum, StrEnum

from sqlalchemy import (  # , Column, Integer, String
    CheckConstraint,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.postgres import Base


class DealType(Base):
    """
    Типы сделок:
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

    __tablename__ = "deal_types"
    type_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="type")
    lead_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="lead_type"
    )


class DealStage(Base):
    """
    Стадии сделок:
    1. NEW - Не разобрано
    2. PREPAYMENT_INVOICE - Выявление потребности
    3. PREPARATION - Заинтересован
    4. EXECUTING - Согласование условий договор
    5. FINAL_INVOICE - Выставление счёта
    6. 1 - На отгрузку
    7. WON - Выиграна
    8. LOSE - Проиграна
    9. APOLOGY - Анализ проигрыша
    """

    __tablename__ = "deal_stages"
    stage_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    order: Mapped[int] = mapped_column(unique=True)  # порядковый номер
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="stage")
    current_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="current_stage"
    )


class Currency(Base):
    """
    Валюты:
    ID    name              cource~ nominal
    RUB - Российский рубль  1       1
    USD - Доллар США        78.4839 1
    EUR - Евро              89.8380 1
    UAH - Гривна            18.8277 10
    BYN - Белорусский рубль 26,3696 1
    KZT - Тенге             15.1277 100
    """

    __tablename__ = "currencies"
    currency_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    cource: Mapped[float]
    nominal: Mapped[int]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="currency"
    )


class Lead(Base):
    """
    Лиды
    """

    __tablename__ = "leads"
    lead_id: Mapped[int] = mapped_column(unique=True)
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="lead")


class Company(Base):
    """
    Компании
    """

    __tablename__ = "companies"
    company_id: Mapped[int] = mapped_column(unique=True)
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="company"
    )


class Contact(Base):
    """
    Контакты
    """

    __tablename__ = "contacts"
    contact_id: Mapped[int] = mapped_column(unique=True)
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="contact"
    )


class User(Base):
    """
    Пользователи
    """

    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    assigned_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="assigned_user"
    )
    created_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="created_user"
    )
    modify_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="modify_user"
    )
    moved_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="moved_user"
    )
    last_activity_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="last_activity_user"
    )
    defect_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="defect_expert"
    )


class Category(Base):
    """
    Направления сделок (воронки):
    0 - общее направление
    1 - сервис
    2 - отгрузка со склада
    """

    __tablename__ = "categories"
    category_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="category"
    )


class StageSemanticEnum(StrEnum):
    """
    Статусы стадии сделки:
    P - В работе
    S - Успешная
    F - Провал
    """

    PROSPECTIVE = "P"
    SUCCESS = "S"
    FAIL = "F"


class Source(Base):
    """
    Источники сделок:
    PARTNER :  Существующий клиент
    19 : Новый клиент
    CALL : Звонок
    WEB : Веб-сайт BOELSHOP
    16 : OZON
    17 : WILDBERRIES
    7 : ЮЛА
    5 : АВИТО
    9|AVITO : Avito - BOEL SHOP AVITO
    STORE : Интернет-магазин
    UC_7VUX6L : Другое
    1|VK : ВКонтакте - Открытая линия
    CALLBACK : Обратный звонок
    WEBFORM : CRM-форма
    12 : Алиэкспресс
    RC_GENERATOR : Генератор продаж
    UC_2THEVX : Шоп и периферия
    REPEAT_SALE : Повторные продажи
    # 20 : Шоурум
    # 21 : Интернет
    """

    __tablename__ = "sources"
    source_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="source")


class CreationSource(Base):
    """
    Источники создания сделок:
    499 : Существующий клиент
    501 : Новый клиент
    503 : Шоурум
    505 : Интернет
    # Ручная / Автоматическая
    """

    __tablename__ = "creation_sources"
    creation_source_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="creation_source"
    )


class MainActivity(Base):
    """
    Основная деятельность клиента:
    147: Дистрибьютор
    149: Домашний пивовар
    151: Завод
    153: Крафт
    155: Наш дилер
    157: Розница
    159: Сети
    161: Торговая компания
    163: Хорека
    """

    __tablename__ = "main_activites"
    main_activity_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="main_activity"
    )


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


class InvoiceStage(Base):
    """
    Стадии счетов:
    1. N - новый
    2. S - отправлен
    3. 1 - выгружен в 1С
    4. P - успешный
    5. D - не оплачен
    """

    __tablename__ = "invoice_stages"
    stage_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    order: Mapped[int] = mapped_column(unique=True)  # порядковый номер
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="invoice_stage"
    )


class Billing(Base):
    """
    Платежи
    """

    __tablename__ = "billings"
    type_bill: Mapped[str]  # нал/безнал
    amount: Mapped[float]
    date_bill: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deal_id: Mapped[str] = mapped_column(ForeignKey("deal.id"))
    deal: Mapped["Deal"] = relationship("Deal", back_populates="billings")


class ShippingCompany(Base):
    """
    Фирмы отгрузки
    439 : Системы
    441 : Элемент
    443 : Торговый дом СР
    445 : ТехТорг
    447 : ИП Гузиков М.Г.
    773 : ИП Воробьев Д.В.
    777 : Эксперты розлива
    """

    __tablename__ = "shipping_companies"
    company_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="shipping_company"
    )


class Warehouse(Base):
    """
    Склады
    597 : Нск
    599 : Спб
    601 : Кдр
    603 : Мск
    """

    __tablename__ = "warehouses"
    warehouse_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="warehouse"
    )


class DefectType(Base):
    """
    Виды неисправностей:
    . - Некомплектная поставка
    . - Некачественная сборка/проверка
    . - Дефект материала
    . - Дефект изготовления комплектующих
    . - Транспортное повреждение
    . - Негарантийная поломка
    """

    __tablename__ = "defect_types"
    defect_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    deal_id: Mapped[str] = mapped_column(ForeignKey("deal.id"))
    deal: Mapped["Deal"] = relationship("Deal", back_populates="defects")


class Deal(Base):
    """Сделки"""

    __tablename__ = "deals"
    __table_args__ = (
        CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
        CheckConstraint(
            "probability IS NULL OR (probability BETWEEN 0 AND 100)",
            name="valid_probability_range",
        ),
        CheckConstraint("deal_id > 0", name="deal_id_positive"),
    )
    deal_id: Mapped[int] = mapped_column(unique=True)  # ID : ид
    title: Mapped[str]  # TITLE : Название
    type_id: Mapped[str] = mapped_column(
        ForeignKey("deal_types.type_id")
    )  # TYPE_ID : Тип сделки
    type: Mapped["DealType"] = relationship("DealType", back_populates="deals")
    stage_id: Mapped[str] = mapped_column(
        ForeignKey("deal_stages.stage_id")
    )  # STAGE_ID : Идентификатор стадии сделки
    stage: Mapped["DealStage"] = relationship(
        "DealStage", back_populates="deals"
    )
    probability: Mapped[int | None]  # PROBABILITY : Вероятность
    currency_id: Mapped[str] = mapped_column(
        ForeignKey("currencies.currency_id")
    )  # CURRENCY_ID : Ид валюты
    currency: Mapped["Currency"] = relationship(
        "Currency", back_populates="deals"
    )
    opportunity: Mapped[float]  # OPPORTUNITY : Сумма
    is_manual_opportunity: Mapped[bool]
    # IS_MANUAL_OPPORTUNITY : Сумма заполнена вручную
    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.lead_id")
    )  # LEAD_ID : Ид лида
    lead: Mapped["Lead"] = relationship("Lead", back_populates="deals")
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.company_id")
    )  # COMPANY_ID : Ид компании
    company: Mapped["Company"] = relationship(
        "Company", back_populates="deals"
    )
    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.contact_id")
    )  # CONTACT_ID : Ид контакта
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="deals"
    )
    begindate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # BEGINDATE : Дата начала (2025-06-18T03:00:00+03:00)
    closedate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # CLOSEDATE : Дата завершения
    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # ASSIGNED_BY_ID : Ид пользователя
    assigned_user: Mapped["User"] = relationship(
        "User", back_populates="assigned_deals"
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # CREATED_BY_ID : Ид пользователя
    created_user: Mapped["User"] = relationship(
        "User", back_populates="created_deals"
    )
    modify_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # MODIFY_BY_ID : Ид пользователя
    modify_user: Mapped["User"] = relationship(
        "User", back_populates="modify_deals"
    )
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # DATE_CREATE : Дата создания
    date_modify: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # DATE_MODIFY : Дата изменения
    opened: Mapped[bool]  # OPENED : Доступен для всех (Y/N)
    closed: Mapped[bool]  # CLOSET : Завершена ли сделка (Y/N)
    comments: Mapped[str | None]  # COMMENTS : Коментарии
    additional_info: Mapped[str | None]
    #  ADDITIONAL_INFO : Дополнительная информация
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id")
    )  # CATEGORY_ID : Идентификатор направления
    category: Mapped["Category"] = relationship(
        "Category", back_populates="deals"
    )
    stage_semantic_id: Mapped[str] = mapped_column(
        PgEnum(
            StageSemanticEnum,
            name="deal_stage_enum",
            create_type=False,
            default=StageSemanticEnum.PROSPECTIVE,
            server_default="P",
        )
    )
    is_new: Mapped[bool]  # IS_NEW : Флаг новой сделки (Y/N)
    is_recurring: Mapped[bool]
    # IS_RECURRING : Флаг шаблона регулярной сделки.
    # Если стоит Y, то это шаблон, а не сделка (Y/N)
    is_return_customer: Mapped[bool]
    # IS_RETURN_CUSTOMER : Признак повторного лида (Y/N)
    is_repeated_approach: Mapped[bool]
    # IS_REPEATED_APPROACH : Повторное обращение (Y/N)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.source_id")
    )  # SOURCE_ID : Идентификатор источника (сводно)
    source: Mapped["Source"] = relationship("Source", back_populates="deals")
    source_description: Mapped[str | None]
    # SOURCE_DESCRIPTION : Дополнительно об источнике
    originator_id: Mapped[str | None]
    # ORIGINATOR_ID : Идентификатор источника данных
    origin_id: Mapped[str | None]
    # ORIGIN_ID : Идентификатор элемента в источнике данных
    moved_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", back_populates="moved_deals"
    )
    moved_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # MOVED_TIME : Дата перемещения элемента на текущую стадию
    last_activity_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # LAST_ACTIVITY_TIME : Время последней активности
    last_communication_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )  # LAST_COMMUNICATION_TIME : Дата ???
    last_activity_by: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # LAST_ACTIVITY_BY : Ид пользователя сделавшего крайнюю за активность
    last_activity_user: Mapped["User"] = relationship(
        "User", back_populates="last_activity_deals"
    )
    main_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("main_activites.main_activity_id")
    )  # UF_CRM_1598883361 : Ид основной деятельности клиента
    main_activity: Mapped["MainActivity"] = relationship(
        "MainActivity", back_populates="deals"
    )
    city: Mapped[str | None]  # UF_CRM_DCT_CITY : Город (населённый пункт)
    source_external: Mapped[str | None]  # UF_CRM_DCT_SOURCE : Источник внешний
    is_shipment_approved: Mapped[bool | None]
    # UF_CRM_60D2AFAEB32CC : Разрешение на отгрузку (1/0)
    lead_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_types.type_id")
    )  # UF_CRM_612463720554B : Тип лида привязанного к сделке
    lead_type: Mapped["DealType"] = relationship(
        "DealType", back_populates="lead_deals"
    )
    payment_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )  # UF_CRM_1632738230 :  Срок оплаты счёта
    payment_type: Mapped[str] = mapped_column(
        PgEnum(
            TypePaymentEnum,
            name="type_payment_enum",
            create_type=False,
            default=TypePaymentEnum.NOT_DEFINE,
            server_default=0,
        )
    )  # UF_CRM_1632738315 : Тип оплаты счёта
    invoice_stage_id: Mapped[str] = mapped_column(
        ForeignKey("invoice_stages.stage_id")
    )  # UF_CRM_1632738354 : Идентификатор стадии счёта
    invoice_stage: Mapped["InvoiceStage"] = relationship(
        "InvoiceStage", back_populates="deals"
    )
    billings: Mapped["Billing"] = relationship(
        "Billing", back_populates="deal"
    )  # UF_CRM_1632738424* : Платёжки по счёту
    is_shipment_approved_invoice: Mapped[bool | None]
    # UF_CRM_1632738559 : Разрешение на отгрузку счёта (1/0)
    current_stage_id: Mapped[str] = mapped_column(
        ForeignKey("deal_stages.stage_id")
    )  # UF_CRM_1632738604 : Идентификатор стадии сделки
    current_stage: Mapped["DealStage"] = relationship(
        "DealStage", back_populates="current_deals"
    )
    shipping_company_id: Mapped[int] = mapped_column(
        ForeignKey("shipping_companies.company_id")
    )  # UF_CRM_1650617036 : Ид фирмы отгрузки
    shipping_company: Mapped["ShippingCompany"] = relationship(
        "ShippingCompany", back_populates="deals"
    )
    creation_source_id: Mapped[int] = mapped_column(
        ForeignKey("creation_sources.creation_source_id")
    )  # UF_CRM_1654577096 : Идентификатор сводного источника (авто/ручной)
    creation_source: Mapped["CreationSource"] = relationship(
        "CreationSource", back_populates="deals"
    )
    shipping_type: Mapped[str] = mapped_column(
        PgEnum(
            TypeShipmentEnum,
            name="type_shipment_enum",
            create_type=False,
            default=TypeShipmentEnum.NOT_DEFINE,
            server_default=0,
        )
    )  # UF_CRM_1655141630 : Тип отгрузки

    # Ссылка на родительскую сделку
    parent_deal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deals.id"), nullable=True
    )  # UF_CRM_1655891443 : Родительская сделка

    # Отношение к связанным сделкам
    related_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="patrnt_deal", remote_side="[Deal.id]"
    )  # UF_CRM_1658467259* : Связанные сделки

    # Отношение к родительской сделке
    parent_deal: Mapped["Deal"] = relationship(
        "Deal",
        back_populates="related_deals",
        remote_side="[Deal.id]",
        foreign_keys="[Deal.parent_deal_id]",
    )
    id_printed_form: Mapped[str | None]
    # UF_CRM_1656227383 : Ид печатной формы
    payment_grace_period: Mapped[int | None]
    # UF_CRM_1656582798 Отсрочка платежа в днях
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.warehouse_id")
    )  # UF_CRM_1659326670 : Ид склада
    warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", back_populates="deals"
    )
    processing_status: Mapped[str] = mapped_column(
        PgEnum(
            ProcessingStatusEnum,
            name="processing_status_enum",
            create_type=False,
            default=ProcessingStatusEnum.NOT_DEFINE,
            server_default=0,
        )
    )  # UF_CRM_1750571370 : Статус обработки

    # Поля сервисных сделок
    defects: Mapped["DefectType"] = relationship(
        "DefectType", back_populates="deal"
    )  # UF_CRM_1655615996118* : Дефекты из списка по сделке
    defect_conclusion: Mapped[str | None]
    # UF_CRM_1655618110493 : Итоговое заключение
    defect_expert_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )  # UF_CRM_1655618547 : Ид эксперта по дефектам
    defect_expert: Mapped["User"] = relationship(
        "User", back_populates="defect_deals"
    )
