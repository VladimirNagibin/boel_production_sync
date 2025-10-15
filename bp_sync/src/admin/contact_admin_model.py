from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.communications import CommunicationChannel
from models.contact_models import Contact

from .base_admin import BaseAdmin
from .mixins import AdminListAndDetailMixin

# from models.references import (
#    ContactType,
#    DealFailureReason,
#    DealType,
#    MainActivity,
#    Source,
# )


class ContactAdmin(
    BaseAdmin, AdminListAndDetailMixin, model=Contact
):  # type: ignore[call-arg]
    name = "Контакт"
    name_plural = "Контакты"
    category = "Сущности"
    icon = "fa-solid fa-user"

    async def get_object_for_details(self, pk: Any) -> Any:
        stmt = (
            select(Contact)
            .options(
                selectinload(Contact.communications).selectinload(
                    CommunicationChannel.channel_type
                ),
                # Загружаем все связанные объекты
                selectinload(Contact.assigned_user),
                selectinload(Contact.created_user),
                selectinload(Contact.modify_user),
                selectinload(Contact.last_activity_user),
                selectinload(Contact.type),
                selectinload(Contact.company),
                selectinload(Contact.lead),
                selectinload(Contact.source),
                selectinload(Contact.main_activity),
                selectinload(Contact.deal_failure_reason),
                selectinload(Contact.deal_type),
                # Загружаем связи со списками
                selectinload(Contact.deals),
                selectinload(Contact.leads),
                selectinload(Contact.companies),
                selectinload(Contact.invoices),
            )
            .where(Contact.id == pk)
        )
        async with self.session_maker(expire_on_commit=False) as session:
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return obj

    column_list = [
        "external_id",
        "name",
        "second_name",
        "last_name",
        "post",
        "company",
        "type",
        "is_deleted_in_bitrix",
    ]

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        "name": AdminListAndDetailMixin.format_title,
        "second_name": AdminListAndDetailMixin.format_title,
        "last_name": AdminListAndDetailMixin.format_title,
        "birthdate": AdminListAndDetailMixin.format_date,
    }

    # Форматтеры для детальной страницы
    column_formatters_detail: dict[str, Any] = {
        "name": AdminListAndDetailMixin.format_title,
        "second_name": AdminListAndDetailMixin.format_title,
        "last_name": AdminListAndDetailMixin.format_title,
        "birthdate": AdminListAndDetailMixin.format_date,
    }

    column_labels = {
        # Основные поля
        "external_id": "Внешний код",
        "name": "Имя",
        "second_name": "Отчество",
        "last_name": "Фамилия",
        "post": "Должность",
        "origin_version": "Версия данных",
        # Статусы и флаги
        "export": "Участвует в экспорте",
        "is_shipment_approved": "Разрешение на отгрузку",
        "is_deleted_in_bitrix": "Удален в Битрикс",
        # Временные метки
        "birthdate": "Дата рождения",
        "date_create": "Дата создания",
        "date_modify": "Дата изменения",
        "last_activity_time": "Дата последней активности",
        "last_communication_time": "Дата последней коммуникации",
        # Коммуникации
        "phones": "Телефоны",
        "emails": "Email",
        "webs": "Сайты",
        "ims": "IM",
        "links": "Ссылки",
        "address": "Адрес",
        "comments": "Комментарии",
        "opened": "Доступен всем",
        # Пользователи
        "assigned_user": "Ответственный",
        "created_user": "Создатель",
        "modify_user": "Изменил",
        "last_activity_user": "Последняя активность",
        # Справочники
        "type": "Тип контакта",
        "type_id": "Тип контакта (ID)",
        "company": "Компания",
        "company_id": "Компания (ID)",
        "lead": "Лид",
        "lead_id": "Лид (ID)",
        "source": "Источник",
        "source_id": "Источник (ID)",
        "main_activity": "Основная деятельность",
        "main_activity_id": "Основная деятельность (ID)",
        "deal_failure_reason": "Причина провала",
        "deal_failure_reason_id": "Причина провала (ID)",
        "deal_type": "Тип сделки",
        "deal_type_id": "Тип сделки (ID)",
        # Связи
        "deals": "Сделки",
        "leads": "Лиды",
        "companies": "Компании",
        "invoices": "Счета",
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
        # Социальные профили
        "wz_instagram": "Instagram",
        "wz_vc": "VK",
        "wz_telegram_username": "Telegram Username",
        "wz_telegram_id": "Telegram ID",
        "wz_avito": "Avito",
        # Дополнительные ответственные
        "additional_responsible": "Доп. ответственные",
    }

    column_sortable_list = [
        "external_id",
        "name",
        "last_name",
        "post",
        "birthdate",
        "date_create",
        "is_deleted_in_bitrix",
    ]

    column_searchable_list = [
        "external_id",
        "name",
        "second_name",
        "last_name",
        "post",
        "address",
        "comments",
    ]

    form_columns = [
        "external_id",
        "name",
        "second_name",
        "last_name",
        "post",
        "is_deleted_in_bitrix",
    ]

    column_details_list = [
        # Основная информация
        "external_id",
        "name",
        "second_name",
        "last_name",
        "post",
        "origin_version",
        # Статусы и флаги
        "export",
        "is_shipment_approved",
        "is_deleted_in_bitrix",
        "opened",
        # Временные метки
        "birthdate",
        "date_create",
        "date_modify",
        "last_activity_time",
        "last_communication_time",
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
        # Справочники
        "type",
        "company",
        "lead",
        "source",
        "main_activity",
        "deal_failure_reason",
        "deal_type",
        # Маркетинговые метки
        "mgo_cc_entry_id",
        "mgo_cc_channel_type",
        "mgo_cc_result",
        "mgo_cc_entry_point",
        "mgo_cc_create",
        "mgo_cc_end",
        "mgo_cc_tag_id",
        "calltouch_site_id",
        "calltouch_call_id",
        "calltouch_request_id",
        # Социальные профили
        "wz_instagram",
        "wz_vc",
        "wz_telegram_username",
        "wz_telegram_id",
        "wz_avito",
        # Связи
        "deals",
        "leads",
        "companies",
        "invoices",
    ]
