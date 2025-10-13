from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.invoice_models import Invoice

from .base_admin import BaseAdmin
from .mixins import AdminListAndDetailMixin

# from models.references import (
#    CreationSource,
#    Currency,
#    DealFailureReason,
#    DealType,
#    InvoiceStage,
#    MainActivity,
#    ShippingCompany,
#    Source,
#    Warehouse,
# )


class InvoiceAdmin(
    BaseAdmin, AdminListAndDetailMixin, model=Invoice
):  # type: ignore[call-arg]
    name = "Счет"
    name_plural = "Счета"
    category = "Финансы"
    icon = "fa-solid fa-file-invoice-dollar"

    async def get_object_for_details(self, pk: Any) -> Any:
        stmt = (
            select(Invoice)
            .options(
                # selectinload(Invoice.communications).selectinload(
                #    CommunicationChannel.channel_type
                # ),
                # Загружаем все связанные объекты
                selectinload(Invoice.assigned_user),
                selectinload(Invoice.created_user),
                selectinload(Invoice.modify_user),
                selectinload(Invoice.last_activity_user),
                selectinload(Invoice.moved_user),
                selectinload(Invoice.currency),
                selectinload(Invoice.company),
                selectinload(Invoice.contact),
                selectinload(Invoice.deal),
                selectinload(Invoice.invoice_stage),
                selectinload(Invoice.previous_stage),
                selectinload(Invoice.current_stage),
                selectinload(Invoice.source),
                selectinload(Invoice.main_activity),
                selectinload(Invoice.warehouse),
                selectinload(Invoice.creation_source),
                selectinload(Invoice.invoice_failure_reason),
                selectinload(Invoice.shipping_company),
                selectinload(Invoice.type),
                selectinload(Invoice.billings),
                selectinload(Invoice.delivery_notes),
            )
            .where(Invoice.id == pk)
        )
        async with self.session_maker(expire_on_commit=False) as session:
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return obj

    column_list = [
        "external_id",
        "title",
        "account_number",
        "opportunity",
        "invoice_stage",
        "company",
        "contact",
        "closedate",
        "is_deleted_in_bitrix",
    ]

    @staticmethod
    def _format_opportunity(model: Invoice, attribute: str) -> str:
        """Форматирование суммы счета"""
        return AdminListAndDetailMixin.format_currency(model, attribute, "₽")

    @staticmethod
    def _format_paid_status(model: Invoice, attribute: str) -> str:
        """Форматирование статуса оплаты"""
        status_map = {
            "paid": "✅ Оплачен",
            "partial": " Частично",
            "unpaid": "❌ Не оплачен",
        }
        return status_map.get(model.paid_status, "Неизвестно")

    @staticmethod
    def _format_paid_percentage(model: Invoice, attribute: str) -> str:
        """Форматирование процента оплаты"""
        return f"{model.paid_percentage}%"

    @staticmethod
    def _format_payment_diff(model: Invoice, attribute: str) -> str:
        """Форматирование оставшейся суммы"""
        return AdminListAndDetailMixin.format_currency(
            model, "payment_diff", "₽"
        )

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        "title": AdminListAndDetailMixin.format_title,
        "opportunity": _format_opportunity,
        "begindate": AdminListAndDetailMixin.format_date,
        "closedate": AdminListAndDetailMixin.format_date,
        "moved_time": AdminListAndDetailMixin.format_date,
    }

    # Форматтеры для детальной страницы
    column_formatters_detail: dict[str, Any] = {
        "title": AdminListAndDetailMixin.format_title,
        "opportunity": _format_opportunity,
        "begindate": AdminListAndDetailMixin.format_date,
        "closedate": AdminListAndDetailMixin.format_date,
        "moved_time": AdminListAndDetailMixin.format_date,
        "last_call_time": AdminListAndDetailMixin.format_date,
        "last_email_time": AdminListAndDetailMixin.format_date,
        "last_imol_time": AdminListAndDetailMixin.format_date,
        "last_webform_time": AdminListAndDetailMixin.format_date,
        "paid_status": _format_paid_status,
        "paid_percentage": _format_paid_percentage,
        "payment_diff": _format_payment_diff,
    }

    column_labels = {
        # Основные поля
        "external_id": "Внешний код",
        "title": "Название счета",
        "account_number": "Номер счета",
        "xml_id": "Внешний код XML",
        "proposal_id": "Предложение",
        "category_id": "Воронка",
        # Статусы и флаги
        "is_manual_opportunity": "Ручной ввод суммы",
        "is_shipment_approved": "Разрешение на отгрузку",
        "check_repeat": "Проверка на повтор",
        "is_loaded": "Выгружено в 1С",
        "is_deleted_in_bitrix": "Удален в Битрикс",
        "opened": "Доступен всем",
        # Финансовые данные
        "opportunity": "Сумма счета",
        "payment_grace_period": "Отсрочка платежа (дни)",
        "total_paid": "Оплачено всего",
        "paid_status": "Статус оплаты",
        "paid_percentage": "Процент оплаты",
        "payment_diff": "Остаток к оплате",
        # Временные метки
        "begindate": "Дата выставления",
        "closedate": "Срок оплаты",
        "moved_time": "Дата изменения стадии",
        "last_call_time": "Дата последнего звонка",
        "last_email_time": "Дата последнего e-mail",
        "last_imol_time": "Дата последнего диалога",
        "last_webform_time": "Дата последней CRM-формы",
        "date_create": "Дата создания",
        "date_modify": "Дата изменения",
        "last_activity_time": "Дата последней активности",
        "last_communication_time": "Дата последней коммуникации",
        # География и источники
        "city": "Город",
        "printed_form_id": "ID печатной формы",
        "source_description": "Описание источника",
        # Перечисляемые типы
        "payment_method": "Форма оплаты",
        "payment_type": "Тип оплаты",
        "shipment_type": "Тип отгрузки",
        # Коммуникации
        "phones": "Телефоны",
        "emails": "Email",
        "webs": "Сайты",
        "ims": "IM",
        "links": "Ссылки",
        "address": "Адрес",
        "comments": "Комментарии",
        # Пользователи
        "assigned_user": "Ответственный",
        "created_user": "Создатель",
        "modify_user": "Изменил",
        "last_activity_user": "Последняя активность",
        "moved_user": "Изменил стадию",
        "moved_by_id": "Изменил стадию (ID)",
        # Справочники
        "currency": "Валюта",
        "currency_id": "Валюта (ID)",
        "company": "Компания",
        "company_id": "Компания (ID)",
        "contact": "Контакт",
        "contact_id": "Контакт (ID)",
        "deal": "Сделка",
        "deal_id": "Сделка (ID)",
        "invoice_stage": "Стадия счета",
        "invoice_stage_id": "Стадия счета (ID)",
        "previous_stage": "Предыдущая стадия",
        "previous_stage_id": "Предыдущая стадия (ID)",
        "current_stage": "Текущая стадия",
        "current_stage_id": "Текущая стадия (ID)",
        "source": "Источник",
        "source_id": "Источник (ID)",
        "main_activity": "Основная деятельность",
        "main_activity_id": "Основная деятельность (ID)",
        "warehouse": "Склад",
        "warehouse_id": "Склад (ID)",
        "creation_source": "Источник создания",
        "creation_source_id": "Источник создания (ID)",
        "invoice_failure_reason": "Причина провала",
        "invoice_failure_reason_id": "Причина провала (ID)",
        "shipping_company": "Фирма отгрузки",
        "shipping_company_id": "Фирма отгрузки (ID)",
        "type": "Тип сделки",
        "type_id": "Тип сделки (ID)",
        # Связи
        "billings": "Платежи",
        "delivery_notes": "Накладные",
        # Маркетинговые метки
        "mgo_cc_entry_id": "MGO CC Entry ID",
        "mgo_cc_channel_type": "MGO CC Channel Type",
        "mgo_cc_result": "MGO CC Result",
        "mgo_cc_entry_point": "MGO CC Entry Point",
        "mgo_cc_create": "MGO CC Create",
        "mgo_cc_end": "MGO CC End",
        "mgo_cc_tag_id": "MGO CC Tag ID",
        "calltouch_site_id": "Calltouch Site ID",
        "calltouch_call_id": "Calltouch Call ID",
        "calltouch_request_id": "Calltouch Request ID",
        "yaclientid": "YaClient ID",
        # Социальные профили
        "wz_instagram": "Instagram",
        "wz_vc": "VK",
        "wz_telegram_username": "Telegram Username",
        "wz_telegram_id": "Telegram ID",
        "wz_avito": "Avito",
    }

    column_sortable_list = [
        "external_id",
        "title",
        "account_number",
        "opportunity",
        "begindate",
        "closedate",
        "date_create",
        "is_deleted_in_bitrix",
    ]

    column_searchable_list = [
        "external_id",
        "title",
        "account_number",
        "xml_id",
        "comments",
    ]

    form_columns = [
        "external_id",
        "title",
        "account_number",
        "opportunity",
        "invoice_stage",
        "is_deleted_in_bitrix",
    ]

    column_details_list = [
        # Основная информация
        "external_id",
        "title",
        "account_number",
        "xml_id",
        "proposal_id",
        "category_id",
        # Финансовая информация
        "opportunity",
        "currency",
        "payment_grace_period",
        "paid_status",
        "paid_percentage",
        "payment_diff",
        "total_paid",
        # Статусы и флаги
        "is_manual_opportunity",
        "is_shipment_approved",
        "check_repeat",
        "is_loaded",
        "is_deleted_in_bitrix",
        "opened",
        # Временные метки
        "begindate",
        "closedate",
        "moved_time",
        "date_create",
        "date_modify",
        "last_activity_time",
        "last_communication_time",
        "last_call_time",
        "last_email_time",
        "last_imol_time",
        "last_webform_time",
        # Перечисляемые типы
        "payment_method",
        "payment_type",
        "shipment_type",
        # Коммуникации
        "phones",
        "emails",
        "webs",
        "ims",
        "links",
        "address",
        "comments",
        # Ответственные пользователи
        "assigned_user",
        "created_user",
        "modify_user",
        "last_activity_user",
        "moved_user",
        # Справочники и связи
        "company",
        "contact",
        "deal",
        "invoice_stage",
        "previous_stage",
        "current_stage",
        "source",
        "main_activity",
        "warehouse",
        "creation_source",
        "invoice_failure_reason",
        "shipping_company",
        "type",
        # Связанные объекты
        "billings",
        "delivery_notes",
        # Дополнительная информация
        "city",
        "printed_form_id",
        "source_description",
    ]
