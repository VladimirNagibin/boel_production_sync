from typing import Any

from models.deal_models import Deal
from models.enums import (
    DualTypePaymentEnum,
    DualTypeShipmentEnum,
    ProcessingStatusEnum,
    StageSemanticEnum,
)

from .base_admin import BaseAdmin
from .mixins import AdminListAndDetailMixin


class DealAdmin(
    BaseAdmin, AdminListAndDetailMixin, model=Deal
):  # type: ignore[call-arg]
    name = "Сделка"
    name_plural = "Сделки"
    category = "Сущности"
    icon = "fa-solid fa-handshake"

    column_list = [  # Поля в списке
        "external_id",
        "title",
        "opportunity",
        "stage",
        "type",
        "creation_source",
        "source",
        "processing_status",
        "is_deleted_in_bitrix",
        "is_frozen",
        "is_setting_source",
        "category",
        "stage_semantic_id",
    ]

    @staticmethod
    def _format_stage_semantic(model: Deal, attribute: str) -> str:
        """Форматирование семантики стадии"""
        return AdminListAndDetailMixin.format_enum_display(
            StageSemanticEnum, model, attribute
        )

    @staticmethod
    def _format_payment_type(model: Deal, attribute: str) -> str:
        """Форматирование типа оплаты"""
        return AdminListAndDetailMixin.format_enum_display(
            DualTypePaymentEnum, model, attribute
        )

    @staticmethod
    def _format_shipment_type(model: Deal, attribute: str) -> str:
        """Форматирование типа отгрузки"""
        return AdminListAndDetailMixin.format_enum_display(
            DualTypeShipmentEnum, model, attribute
        )

    @staticmethod
    def _format_processing_status(model: Deal, attribute: str) -> str:
        """Форматирование статуса обработки"""
        return AdminListAndDetailMixin.format_enum_display(
            ProcessingStatusEnum, model, attribute
        )

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        "title": AdminListAndDetailMixin.format_title,
        "opportunity": AdminListAndDetailMixin.format_title,
        "stage_semantic_id": _format_stage_semantic,
    }

    # Форматтеры для детальной страницы (показываем display_name)
    column_formatters_detail: dict[str, Any] = {
        "stage_semantic_id": _format_stage_semantic,
        "payment_type": _format_payment_type,
        "shipment_type": _format_shipment_type,
        "processing_status": _format_processing_status,
    }

    column_labels = {  # Надписи полей в списке # type: ignore
        "external_id": "Внешний код",
        "title": "Название",
        "opportunity": "Сумма",
        "category": "Воронка",
        "stage": "Стадия",
        "type": "Тип",
        "creation_source": "Источник сводно",
        "source": "Источник",
        "processing_status": "Статус обработки",
        "is_deleted_in_bitrix": "Удалён в Б24",
        "is_frozen": "Заморожен",
        "is_setting_source": "Источники вручную",
        "assigned_user": "Ответственный",
        "created_user": "Создатель",
        "modify_user": "Изменил",
        "last_activity_user": "Последняя активность",
        "date_create": "Дата создания",
        "date_modify": "Дата изменения",
        "last_activity_time": "Дата последней активности",
        "last_communication_time": "Дата последней коммуникации",
        "additional_info": "Дополнительная информация",
        "stage_semantic_id": "Семантика стадии",
        "payment_type": "Тип оплаты",
        "begindate": "Дата начала сделки",
        "closedate": "Дата завершения сделки",
        "moved_time": "Время перемещения сделки",
        "payment_deadline": "Срок оплаты сделки",
        "shipment_type": "Тип отгрузки",
        "invoices": "Счета",
        "timeline_comments": "Комментарии из ленты",
        "company": "Компания",
        "contact": "Контакт",
        "lead": "Лид",
        "main_activity": "Основная деятельность",
        "invoice_stage": "Стадия счёта",
        "current_stage": "Предыдущая стадия",
        "shipping_company": "Фирма отгрузки",
        "warehouse": "Склад",
        "add_info": "Дополнительная информация",
    }
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "title",
        "opportunity",
        "processing_status",
        "is_deleted_in_bitrix",
        "is_frozen",
        "is_setting_source",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "external_id",
        "title",
    ]
    form_columns = [  # Поля на форме редактирования
        "external_id",
        "title",
        "processing_status",
        "is_deleted_in_bitrix",
        "is_frozen",
        "is_setting_source",
    ]
    column_details_list = [  # Поля на форме просмотра
        "external_id",
        "title",
        "opportunity",
        "category",
        "stage",
        "type",
        "creation_source",
        "source",
        "processing_status",
        "is_deleted_in_bitrix",
        "is_frozen",
        "is_setting_source",
        "assigned_user",
        "created_user",
        "modify_user",
        "last_activity_user",
        "begindate",
        "closedate",
        "moved_time",
        "payment_deadline",
        "date_create",
        "date_modify",
        "last_activity_time",
        "last_communication_time",
        "additional_info",
        "stage_semantic_id",
        "payment_type",
        "shipment_type",
        "invoices",
        "timeline_comments",
        "company",
        "contact",
        "lead",
        "main_activity",
        "invoice_stage",
        "current_stage",
        "shipping_company",
        "warehouse",
        "add_info",
    ]

    form_args = {
        "stage_semantic_id": {
            "choices": [
                (member.value, member.get_display_name(member.value))
                for member in StageSemanticEnum
            ]
        }
    }

    # Или через form_choices (альтернативный способ)
    # form_choices = {
    #    "stage_semantic_id": [
    #        (member.value, member.get_display_name(member.value))
    #        for member in StageSemanticEnum
    #    ]
    # }

    # form_ajax_refs = {  # Поиск поля по значению из списка
    # "currency": {
    #    "fields": ["name", "external_id"],
    #    "page_size": 10,
    #    "placeholder": "Search currency...",
    #    "minimum_input_length": 2
    # },
    # "company_type": {"fields": ["name"]},
    # "contact": {"fields": ["name", "last_name"]},
    # }
