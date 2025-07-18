from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import BusinessEntity, EntityType
from .company_models import Company
from .contact_models import Contact
from .deal_documents import Billing
from .enums import (  # TypePaymentEnum,; TypeShipmentEnum,
    DualTypePayment,
    DualTypePaymentEnum,
    DualTypeShipment,
    DualTypeShipmentEnum,
    ProcessingStatusEnum,
    StageSemanticEnum,
)
from .invoice_models import Invoice
from .lead_models import Lead
from .references import (
    Category,
    CreationSource,
    Currency,
    DealFailureReason,
    DealStage,
    DealType,
    DefectType,
    InvoiceStage,
    MainActivity,
    ShippingCompany,
    Source,
    Warehouse,
)
from .user_models import User


class Deal(BusinessEntity):
    """Сделки"""

    __tablename__ = "deals"
    __table_args__ = (
        CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
        CheckConstraint(
            "probability IS NULL OR (probability BETWEEN 0 AND 100)",
            name="valid_probability_range",
        ),
        CheckConstraint("external_id > 0", name="external_id_positive"),
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.DEAL

    @property
    def tablename(self) -> str:
        return self.__tablename__

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название сделки"
    )  # TITLE : Название
    additional_info: Mapped[str | None] = mapped_column(
        comment="Дополнительная информация"
    )  # ADDITIONAL_INFO : Дополнительная информация

    # Статусы и флаги
    probability: Mapped[int | None] = mapped_column(
        comment="Вероятность успеха (0-100)"
    )  # PROBABILITY : Вероятность
    is_manual_opportunity: Mapped[bool] = mapped_column(
        default=False, comment="Ручной ввод суммы"
    )  # IS_MANUAL_OPPORTUNITY : Сумма заполнена вручную
    closed: Mapped[bool] = mapped_column(
        default=False, comment="Завершена"
    )  # CLOSET : Завершена ли сделка (Y/N)
    is_new: Mapped[bool] = mapped_column(
        default=False, comment="Новая сделка"
    )  # IS_NEW : Флаг новой сделки (Y/N)
    is_recurring: Mapped[bool] = mapped_column(
        default=False, comment="Регулярная сделка"
    )  # IS_RECURRING : Флаг шаблона регулярной сдели. Если Y, то шаблон (Y/N)
    is_return_customer: Mapped[bool] = mapped_column(
        default=False, comment="Повторный клиент"
    )  # IS_RETURN_CUSTOMER : Признак повторного лида (Y/N)
    is_repeated_approach: Mapped[bool] = mapped_column(
        default=False, comment="Повторное обращение"
    )  # IS_REPEATED_APPROACH : Повторное обращение (Y/N)
    is_shipment_approved: Mapped[bool | None] = mapped_column(
        comment="Разрешение на отгрузку"
    )  # UF_CRM_60D2AFAEB32CC : Разрешение на отгрузку (1/0)
    is_shipment_approved_invoice: Mapped[bool | None] = mapped_column(
        comment="Разрешение на отгрузку счета"
    )  # UF_CRM_1632738559 : Разрешение на отгрузку счёта (1/0)

    # Финансовые данные
    opportunity: Mapped[float] = mapped_column(
        default=0.0, comment="Сумма сделки"
    )  # OPPORTUNITY : Сумма
    payment_grace_period: Mapped[int | None] = mapped_column(
        comment="Отсрочка платежа (дни)"
    )  # UF_CRM_1656582798 Отсрочка платежа в днях
    billings: Mapped["Billing"] = relationship(
        "Billing", back_populates="deal"
    )  # UF_CRM_1632738424* : Платёжки по счёту

    # Временные метки
    begindate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата начала"
    )  # BEGINDATE : Дата начала (2025-06-18T03:00:00+03:00)
    closedate: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата завершения"
    )  # CLOSEDATE : Дата завершения
    moved_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Время перемещения"
    )  # MOVED_TIME : Дата перемещения элемента на текущую стадию
    payment_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Срок оплаты"
    )  # UF_CRM_1632738230 :  Срок оплаты счёта

    # География и источники
    printed_form_id: Mapped[str | None] = mapped_column(
        comment="ID печатной формы"
    )  # UF_CRM_1656227383 : Ид печатной формы(доставка)

    # Перечисляемые типы
    stage_semantic_id: Mapped[StageSemanticEnum] = mapped_column(
        PgEnum(
            StageSemanticEnum,
            name="deal_stage_enum",
            create_type=False,
            default=StageSemanticEnum.PROSPECTIVE,
            server_default=StageSemanticEnum.PROSPECTIVE.value,
        ),
        comment="Семантика стадии",
    )  # STAGE_SEMANTIC_ID : Статусы стадии сделки
    # payment_type: Mapped[TypePaymentEnum] = mapped_column(
    #    PgEnum(
    #        TypePaymentEnum,
    #        name="type_payment_enum",
    #        create_type=False,
    #        default=TypePaymentEnum.NOT_DEFINE,
    #        server_default=0,
    #    ),
    #    comment="Тип оплаты",
    # )  # UF_CRM_1632738315 : Тип оплаты счёта
    payment_type: Mapped[DualTypePaymentEnum] = mapped_column(
        DualTypePayment(value_type="deals"),
        comment="Тип оплаты",
    )  # UF_CRM_1632738315 : Тип оплаты счёта

    # shipping_type: Mapped[TypeShipmentEnum] = mapped_column(
    #    PgEnum(
    #        TypeShipmentEnum,
    #        name="type_shipment_enum",
    #        create_type=False,
    #        default=TypeShipmentEnum.NOT_DEFINE,
    #        server_default=0,
    #    ),
    #    comment="Тип отгрузки",
    # )  # UF_CRM_1655141630 : Тип отгрузки
    shipment_type: Mapped[DualTypeShipmentEnum] = mapped_column(
        DualTypeShipment(value_type="deals"), comment="Тип отгрузки для сделок"
    )
    processing_status: Mapped[ProcessingStatusEnum] = mapped_column(
        PgEnum(
            ProcessingStatusEnum,
            name="processing_status_enum",
            create_type=False,
            default=ProcessingStatusEnum.NOT_DEFINE,
            server_default=0,
        ),
        comment="Статус обработки",
    )  # UF_CRM_1750571370 : Статус обработки

    # Связи с другими сущностями
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="deal"
    )
    currency_id: Mapped[str | None] = mapped_column(
        ForeignKey("currencies.external_id")
    )  # CURRENCY_ID : Ид валюты
    currency: Mapped["Currency"] = relationship(
        "Currency", back_populates="deals"
    )
    type_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_types.external_id")
    )  # TYPE_ID : Тип сделки
    type: Mapped["DealType"] = relationship("DealType", back_populates="deals")
    stage_id: Mapped[str] = mapped_column(
        ForeignKey("deal_stages.external_id")
    )  # STAGE_ID : Идентификатор стадии сделки
    stage: Mapped["DealStage"] = relationship(
        "DealStage", back_populates="deals"
    )
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.external_id")
    )  # LEAD_ID : Ид лида
    lead: Mapped["Lead"] = relationship("Lead", back_populates="deals")
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id")
    )  # COMPANY_ID : Ид компании
    company: Mapped["Company"] = relationship(
        "Company", back_populates="deals"
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.external_id")
    )  # CONTACT_ID : Ид контакта
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="deals"
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.external_id")
    )  # CATEGORY_ID : Идентификатор направления
    category: Mapped["Category"] = relationship(
        "Category", back_populates="deals"
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.external_id")
    )  # SOURCE_ID : Идентификатор источника (сводно)
    source: Mapped["Source"] = relationship("Source", back_populates="deals")
    main_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("main_activites.external_id")
    )  # UF_CRM_1598883361 : Ид основной деятельности клиента
    main_activity: Mapped["MainActivity"] = relationship(
        "MainActivity", back_populates="deals"
    )
    lead_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_types.external_id")
    )  # UF_CRM_612463720554B : Тип лида привязанного к сделке
    lead_type: Mapped["DealType"] = relationship(
        "DealType", back_populates="lead_deals"
    )
    invoice_stage_id: Mapped[str | None] = mapped_column(
        ForeignKey("invoice_stages.external_id")
    )  # UF_CRM_1632738354 : Идентификатор стадии счёта
    invoice_stage: Mapped["InvoiceStage"] = relationship(
        "InvoiceStage", back_populates="deals"
    )
    current_stage_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_stages.external_id")
    )  # UF_CRM_1632738604 : Ид стадии сделки (для фиксации предыдущей стадии)
    current_stage: Mapped["DealStage"] = relationship(
        "DealStage", back_populates="current_deals"
    )
    shipping_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipping_companies.ext_alt_id")
    )  # UF_CRM_1650617036 : Ид фирмы отгрузки
    shipping_company: Mapped["ShippingCompany"] = relationship(
        "ShippingCompany", back_populates="deals"
    )
    creation_source_id: Mapped[int | None] = mapped_column(
        ForeignKey("creation_sources.external_id")
    )  # UF_CRM_1654577096 : Идентификатор сводного источника (авто/ручной)
    creation_source: Mapped["CreationSource"] = relationship(
        "CreationSource", back_populates="deals"
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.external_id")
    )  # UF_CRM_1659326670 : Ид склада
    warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", back_populates="deals"
    )
    deal_failure_reason_id: Mapped[int | None] = mapped_column(
        ForeignKey("deal_failure_reasons.external_id")
    )  # UF_CRM_652940014E9A5 : Ид причины провала
    deal_failure_reason: Mapped["DealFailureReason"] = relationship(
        "DealFailureReason", back_populates="deals"
    )

    # Пользователи
    moved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID переместившего",
    )  # MOVED_BY_ID : Ид автора, который переместил элемент на текущую стадию
    moved_user: Mapped["User"] = relationship(
        "User", foreign_keys=[moved_by_id], back_populates="moved_deals"
    )
    defect_expert_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="ID эксперта по дефектам",
    )  # UF_CRM_1655618547 : Ид эксперта по дефектам
    defect_expert: Mapped["User"] = relationship(
        "User", foreign_keys=[defect_expert_id], back_populates="defect_deals"
    )

    # Поля сервисных сделок
    defects: Mapped["DefectType"] = relationship(
        "DefectType", back_populates="deal"
    )  # UF_CRM_1655615996118* : Дефекты из списка по сделке
    defect_conclusion: Mapped[str | None] = mapped_column(
        comment="Заключение по дефектам"
    )  # UF_CRM_1655618110493 : Итоговое заключение

    # Связанные сделки (доставка)
    parent_deal_id: Mapped[int | None] = mapped_column(
        ForeignKey("deals.external_id"), nullable=True
    )  # UF_CRM_1655891443 : Родительская сделка
    related_deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="parent_deal", remote_side="[parent_deal_id]"
    )  # UF_CRM_1658467259* : Связанные сделки
    parent_deal: Mapped["Deal | None"] = relationship(
        "Deal",
        back_populates="related_deals",
        remote_side="[Deal.id]",
        # foreign_keys="[Deal.parent_deal_id]",
    )  # Отношение к родительской сделке

    # Маркетинговые метки
    yaclientid: Mapped[str | None] = mapped_column(
        comment="yaclientid"
    )  # UF_CRM_1739185983784 : yaclientid

    """ remaining fields:
    "TAX_VALUE": double, Ставка налога
    "QUOTE_ID": int, Идентификатор квоты
    "LOCATION_ID": int, Местоположение клиента

    "UF_CRM_1598883220": str, Промывочная жидкость клиента
    "UF_CRM_1598883274": list, Пеногасители клиента
    "UF_CRM_1617951428": list,	ТК клиента

    "UF_CRM_ZOOM_MEET_LINK": str, Ссылка на Zoom
    "UF_CRM_ZOOM_MEET_TZ": str, Дата/время Zoom

    "UF_CRM_DCT_UID": ДКТ: client_id
    "UF_CRM_DCT_CID": ДКТ: client_cid
    "UF_CRM_DCT_YA_CID": ДКТ: ya_client_id
    "UF_CRM_DCT_MEDIUM": ДКТ: Канал
    "UF_CRM_DCT_CAMPAIGN": ДКТ: Кампания
    "UF_CRM_DCT_CONTENT": ДКТ: Содержимое
    "UF_CRM_DCT_TERM": ДКТ: Что искал
    "UF_CRM_DCT_DURATION": ДКТ: Время на сайте
    "UF_CRM_DCT_PAGE": ДКТ: Страница звонка
    "UF_CRM_DCT_CONTEXT": ДКТ: Контекст вызова
    "UF_CRM_DCT_CUSTOM": ДКТ: Custom
    "UF_CRM_DCT_WID_NAME": ДКТ: Имя виджета
    "UF_CRM_DCT_TYPE": ДКТ: Тип заявки
    "UF_CRM_DCT_SID": ДКТ: client_sid

    "UF_CRM_ROISTAT": riostat

    "UF_CRM_1657360424": html ссылка
    """
