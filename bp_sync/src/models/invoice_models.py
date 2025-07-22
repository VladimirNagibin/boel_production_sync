from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import BusinessEntityCore, EntityType
from .company_models import Company
from .contact_models import Contact
from .deal_documents import Billing
from .enums import (
    DualTypePayment,
    DualTypePaymentEnum,
    DualTypeShipment,
    DualTypeShipmentEnum,
    MethodPaymentEnum,
)
from .references import (
    CreationSource,
    Currency,
    DealFailureReason,
    DealType,
    InvoiceStage,
    MainActivity,
    ShippingCompany,
    Source,
    Warehouse,
)
from .user_models import User

if TYPE_CHECKING:
    from .deal_models import Deal


class Invoice(BusinessEntityCore):
    """
    Счета
    """

    __tablename__ = "invoices"

    # __table_args__ = (
    #    CheckConstraint("opportunity >= 0", name="non_negative_opportunity"),
    #    CheckConstraint(
    #        "probability IS NULL OR (probability BETWEEN 0 AND 100)",
    #        name="valid_probability_range",
    #    ),
    #    CheckConstraint("external_id > 0", name="external_id_positive"),
    # )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.INVOICE

    @property
    def tablename(self) -> str:
        return self.__tablename__

    # Идентификаторы и основные данные
    title: Mapped[str] = mapped_column(
        comment="Название сделки"
    )  # title : Название
    account_number: Mapped[str | None] = mapped_column(
        comment="Номер счёта"
    )  # accountNumber : Номер счёта
    xml_id: Mapped[str | None] = mapped_column(
        comment="Внешний код"
    )  # xmlId : Внешний код
    proposal_id: Mapped[int | None] = mapped_column(
        comment="Предложение"
    )  # parentId7 : Предложение*
    category_id: Mapped[int | None] = mapped_column(
        comment="Воронка"
    )  # categoryId : Воронка

    # Статусы и флаги
    is_manual_opportunity: Mapped[bool] = mapped_column(
        default=False, comment="Ручной ввод суммы"
    )  # isManualOpportunity : Сумма заполнена вручную
    is_shipment_approved: Mapped[bool | None] = mapped_column(
        comment="Разрешение на отгрузку"
    )  # ufCrm_62B53CC589745 : Разрешение на отгрузку (Y/N)
    check_repeat: Mapped[bool | None] = mapped_column(
        comment="Счёт проверка на повтор"
    )  # ufCrm_SMART_INVOICE_1651138836085 : Счёт проверка на повтор (Y/N)
    is_loaded: Mapped[bool | None] = mapped_column(
        default=False, comment="Выгружено в 1с"
    )  # webformId : Создано CRM-формой (1 - True)

    # Финансовые данные
    opportunity: Mapped[float] = mapped_column(
        default=0.0, comment="Сумма сделки"
    )  # opportunity : Сумма
    payment_grace_period: Mapped[int | None] = mapped_column(
        comment="Отсрочка платежа (дни)"
    )  # ufCrm_SMART_INVOICE_1656584515597 Отсрочка платежа в днях
    # billings: Mapped["Billing"] = relationship(
    #    "Billing", back_populates="invoice"
    # )  # ufCrm_SMART_INVOICE_1651116689037* : Платёжки по счёту

    # Временные метки
    begindate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата выставления"
    )  # begindate : Дата выставления (2025-06-18T03:00:00+03:00)
    closedate: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Срок оплаты"
    )  # closedate : Срок оплаты
    moved_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата изменения стадии"
    )  # movedTime : Дата изменения стадии
    last_call_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата последнего звонка"
    )  # lastCommunicationCallTime :  Дата последнего звонка
    last_email_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата последнего e-mail"
    )  # lastCommunicationEmailTime :  Дата последнего e-mail
    last_imol_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="Дата последнего диалога в открытой линии",
    )  # lastCommunicationImolTime :  Дата последнего диалога в открытой линии
    last_webform_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата последнего заполнения CRM-формы"
    )  # lastCommunicationWebformTime :  Дата последнего заполнения CRM-формы

    # География и источники
    printed_form_id: Mapped[str | None] = mapped_column(
        comment="ID печатной формы"
    )  # ufCrm_SMART_INVOICE_1651138396589 : ИД печатной формы

    # Перечисляемые типы
    payment_method: Mapped[MethodPaymentEnum] = mapped_column(
        PgEnum(
            MethodPaymentEnum,
            name="payment_method_enum",
            create_type=False,
            default=MethodPaymentEnum.NOT_DEFINE,
            server_default=MethodPaymentEnum.NOT_DEFINE.value,
        ),
        comment="форма оплаты",
    )  # ufCrm_SMART_INVOICE_1651083629638 : форма оплаты
    payment_type: Mapped[DualTypePaymentEnum] = mapped_column(
        DualTypePayment(value_type="invoices"),
        comment="Тип оплаты",
    )  # ufCrm_SMART_INVOICE_1651114959541 : Тип оплаты счёта
    shipment_type: Mapped[DualTypeShipmentEnum] = mapped_column(
        DualTypeShipment(value_type="invoices"),
        comment="Тип отгрузки для счетов",
    )  # ufCrm_62B53CC5A2EDF : Тип отгрузки

    # Связи с другими сущностями
    currency_id: Mapped[str | None] = mapped_column(
        ForeignKey("currencies.external_id")
    )  # currencyId : Ид валюты
    currency: Mapped["Currency"] = relationship(
        "Currency", back_populates="invoices"
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.external_id")
    )  # companyId : Ид компании
    company: Mapped["Company"] = relationship(
        "Company", back_populates="invoices"
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.external_id")
    )  # contactId : Ид контакта
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="invoices"
    )
    deal_id: Mapped[int | None] = mapped_column(
        ForeignKey("deals.external_id")
    )  # parentId2 : Ид лида
    deal: Mapped["Deal"] = relationship("Deal", back_populates="invoices")
    invoice_stage_id: Mapped[str | None] = mapped_column(
        ForeignKey("invoice_stages.external_id")
    )  # stageId : Идентификатор стадии счёта
    invoice_stage: Mapped["InvoiceStage"] = relationship(
        "InvoiceStage", back_populates="invoices"
    )
    previous_stage_id: Mapped[str | None] = mapped_column(
        ForeignKey("invoice_stages.external_id")
    )  # previousStageId : Предыдущая стадия
    previous_stage: Mapped["InvoiceStage"] = relationship(
        "InvoiceStage", back_populates="invoices"
    )
    current_stage_id: Mapped[str | None] = mapped_column(
        ForeignKey("invoice_stages.external_id")
    )  # ufCrm_SMART_INVOICE_1651509493 : Идентификатор стадии счёта
    current_stage: Mapped["InvoiceStage"] = relationship(
        "InvoiceStage", back_populates="invoices"
    )
    source_id: Mapped[str | None] = mapped_column(
        ForeignKey("sources.external_id")
    )  # sourceId : Идентификатор источника
    source: Mapped["Source"] = relationship(
        "Source", back_populates="invoices"
    )
    main_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("main_activites.ext_alt4_id")
    )  # ufCrm_6260D1A85BBB9 : Ид основной деятельности клиента
    main_activity: Mapped["MainActivity"] = relationship(
        "MainActivity", back_populates="invoices"
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.ext_alt_id")
    )  # ufCrm_SMART_INVOICE_1651083239729 : Ид склада
    warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", back_populates="invoices"
    )
    creation_source_id: Mapped[int | None] = mapped_column(
        ForeignKey("creation_sources.ext_alt_id")
    )  # ufCrm_62B53CC5943F6 : Идентификатор сводного источника (авто/ручной)
    creation_source: Mapped["CreationSource"] = relationship(
        "CreationSource", back_populates="invoices"
    )
    invoice_failure_reason_id: Mapped[int | None] = mapped_column(
        ForeignKey("deal_failure_reasons.ext_alt4_id")
    )  # ufCrm_6721D5B0EE615 : Ид причины провала
    invoice_failure_reason: Mapped["DealFailureReason"] = relationship(
        "DealFailureReason", back_populates="invoices"
    )
    shipping_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipping_companies.external_id")
    )  # mycompanyId : Реквизиты вашей компании
    shipping_company: Mapped["ShippingCompany"] = relationship(
        "ShippingCompany", back_populates="invoices"
    )
    type_id: Mapped[str | None] = mapped_column(
        ForeignKey("deal_types.external_id")
    )  # ufCrm_6260D1A936963 : Тип лида ???
    type: Mapped["DealType"] = relationship(
        "DealType", back_populates="invoices"
    )

    # Пользователи
    moved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.external_id"),
        comment="Кто изменил стадию",
    )  # movedBy : Кто изменил стадию
    moved_user: Mapped["User"] = relationship(
        "User", foreign_keys=[moved_by_id], back_populates="moved_deals"
    )

    # Маркетинговые метки
    yaclientid: Mapped[str | None] = mapped_column(
        comment="yaclientid"
    )  # ufCrm_67AC443A81F1C : yaclientid

    billings: Mapped[list["Billing"]] = relationship(
        "Billing", back_populates="invoice"
    )  # ufCrm_SMART_INVOICE_1651116689037* : Счет платежи

    @property
    def total_paid(self) -> float:
        """Общая сумма оплаченных платежей"""
        return (
            sum(billing.amount for billing in self.billings)
            if self.billings
            else 0.0
        )

    @property
    def paid_status(self) -> str:
        """Статус оплаты:
        - 'paid' - полностью оплачена
        - 'partial' - частично оплачена
        - 'unpaid' - не оплачена
        """
        total_paid = self.total_paid

        if abs(total_paid - self.opportunity) < 0.01:
            return "paid"
        elif total_paid > 0:
            return "partial"
        else:
            return "unpaid"

    @property
    def paid_percentage(self) -> float:
        """Процент оплаты от общей суммы"""
        if self.opportunity > 0:
            return float(
                min(
                    100.0, round((self.total_paid / self.opportunity) * 100, 2)
                )
            )
        return 0.0

    @property
    def payment_diff(self) -> float:
        """Оставшаяся сумма к оплате"""
        return float(max(0.0, self.opportunity - self.total_paid))

    """ remaining fields:
    contactIds		{8}	list crm_contact_id	Контакты
    contacts		{8}	list crm_contact	Контакты
    observers		{8}	list user	Наблюдатели
    taxValue		{8}	float	Сумма налога
    locationId		{8}	location	Местоположение
    ufCrm_6260D1A83E869		{12}	str	Промывочная жидкость клиента
    ufCrm_6260D1A84AD9F		{13}	enumeration	Пеногасители клиента
    ufCrm_6260D1A86AFAA		{12}	str	Ссылка на Zoom
    ufCrm_6260D1A871777		{12}	str	Дата/время Zoom
    ufCrm_6260D1A87BECE		{12}	str	ДКТ: client_id
    ufCrm_6260D1A887BC2		{12}	str	ДКТ: client_cid
    ufCrm_6260D1A8934A4		{12}	str	ДКТ: ya_client_id
    ufCrm_6260D1A8B127B		{12}	str	ДКТ: Канал
    ufCrm_6260D1A8B9660		{12}	str	ДКТ: Кампания
    ufCrm_6260D1A8C46A7		{12}	str	ДКТ: Содержимое
    ufCrm_6260D1A8D1202		{12}	str	ДКТ: Что искал
    ufCrm_6260D1A8DC432		{12}	str	ДКТ: Время на сайте
    ufCrm_6260D1A8E51FC		{12}	str	ДКТ: Страница звонка
    ufCrm_6260D1A8EF054		{12}	str	ДКТ: Контекст вызова
    ufCrm_6260D1A9036CA		{12}	str	ДКТ: Custom
    ufCrm_6260D1A90CB30		{12}	str	ДКТ: Имя виджета
    ufCrm_6260D1A914AEC		{12}	str	ДКТ: Тип заявки
    ufCrm_6260D1A91F709		{12}	str	riostat
    ufCrm_6260D1A927C19		{13}	enumeration	ТК клиента
    ufCrm_6260D1A94068D		{13}	crm_status	Тек стадия
    ufCrm_6260F706612FC		{12}	bool	Проверка на повтор
    ufCrm_6260F70671097		{12}	date	Счет срок оплаты
    ufCrm_6260F70679988		{13}	enumeration	Счет тип оплаты
    ufCrm_6260F70685E40		{13}	crm_status	Счет тек стадия
    ufCrm_6260F7068F7FA		{12}	list[str]	Счет платежи
    ufCrm_6260F7069E93B		{12}	bool	Счет проверка на повтор
    ufCrm_626808D5142A6		{13}	enumeration	Фирма отгрузки
    ufCrm_62B53CC5AFAE0		{12}	list[file]	Информация о  проблеме (файлы)
    ufCrm_62B53CC5BF73E		{13}	enumeration	Вид неисправности
    ufCrm_62B53CC5D26A5		{12}	str	Итоговое заключение
    ufCrm_62B53CC5DBADF		{12}	employee	Эксперт
    ufCrm_62B53CC5E337D		{12}	crm	Связанная сделка
    ufCrm_62B929B8439D6		{12}	str	Печатная форма
    ufCrm_6721D5AD3DD9E		{12}	url	Ссылка
    ufCrm_6721D5AD7933B		{12}	list[crm]	Связанные сделки
    ufCrm_6721D5ADB5532		{13}	enumeration	Склад
    ufCrm_6721D5B13DFAB		{12}	str	ДКТ: client_sid
    ufCrm_SMART_INVOICE_1651116689037		{12}	list[str]	Счёт платежи
    """
