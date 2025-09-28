from typing import Any

from sqladmin import Admin, ModelView

from models.communications import (  # noqa: F401
    CommunicationChannel,
    CommunicationChannelType,
)
from models.company_models import Company  # noqa: F401
from models.contact_models import Contact  # noqa: F401
from models.deal_documents import Billing, Contract  # noqa: F401
from models.deal_models import AdditionalInfo, Deal  # noqa: F401
from models.delivery_note_models import DeliveryNote  # noqa: F401
from models.enums import (
    DualTypePaymentEnum,
    DualTypeShipmentEnum,
    ProcessingStatusEnum,
    StageSemanticEnum,
)
from models.invoice_models import Invoice  # noqa: F401
from models.lead_models import Lead  # noqa: F401
from models.references import (  # noqa: F401
    AdditionalResponsible,
    Category,
    ContactType,
    CreationSource,
    Currency,
    DealFailureReason,
    DealStage,
    DealType,
    DefectType,
    Department,
    Emploees,
    Industry,
    InvoiceStage,
    LeadStatus,
    MainActivity,
    ShippingCompany,
    Source,
    Warehouse,
)
from models.timeline_comment_models import TimelineComment
from models.user_models import Manager, User  # noqa: F401

# from wtforms import Form, StringField
# from wtforms.validators import Optional
# from sqlalchemy.ext.asyncio import AsyncSession
# from db.postgres import get_session


# Базовые модели
class BaseAdmin(ModelView):  # type: ignore[misc]
    page_size = 50
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    can_view_details = True
    icon = "fa-solid fa-table"


# Основные сущности
class DealAdmin(BaseAdmin, model=Deal):  # type: ignore[call-arg]
    name = "Сделка"
    name_plural = "Сделки"
    category = "Сущности"

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

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        "title": lambda m, a: (
            str(getattr(m, a, ""))[:35] + "..."
            if len(str(getattr(m, a, ""))) > 35
            else str(getattr(m, a, ""))
        ),
        "opportunity": lambda m, a: (
            f"{getattr(m, a, 0):,.2f}" if getattr(m, a, 0) else "0"
        ),
        "stage_semantic_id": lambda m, a: (
            StageSemanticEnum.get_display_name(getattr(m, a, ""))
            if getattr(m, a, "")
            else "Не указано"
        ),
    }

    # Форматтеры для детальной страницы (показываем display_name)
    column_formatters_detail: dict[str, Any] = {
        "stage_semantic_id": lambda m, a: (
            StageSemanticEnum.get_display_name(getattr(m, a, ""))
            if getattr(m, a, "")
            else "Не указано"
        ),
        "payment_type": lambda m, a: (
            DualTypePaymentEnum.get_display_name(
                getattr(m, a, "")  # type: ignore[arg-type]
            )
            if getattr(m, a, "")
            else "Не указано"
        ),
        "shipment_type": lambda m, a: (
            DualTypeShipmentEnum.get_display_name(
                getattr(m, a, "")  # type: ignore[arg-type]
            )
            if getattr(m, a, "")
            else "Не указано"
        ),
        "processing_status": lambda m, a: (
            ProcessingStatusEnum.get_display_name(
                getattr(m, a, "")  # type: ignore[arg-type]
            )
            if getattr(m, a, "")
            else "Не указано"
        ),
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
    column_default_sort = [  # Сортировка по умолчанию # type: ignore
        ("external_id", True)
    ]
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
    form_choices = {
        "stage_semantic_id": [
            (member.value, member.get_display_name(member.value))
            for member in StageSemanticEnum
        ]
    }

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
    icon = "fa-solid fa-handshake"


class CompanyAdmin(BaseAdmin, model=Company):  # type: ignore[call-arg]
    name = "Компания"
    name_plural = "Компании"
    category = "Сущности"

    column_list = [  # Поля в списке
        "external_id",
        "title",
        "is_my_company",
        "revenue",
        "industry",
        "employees",
        "source",
    ]

    # Форматирование значений
    column_formatters: dict[str, Any] = {
        "title": lambda m, a: (
            str(getattr(m, a, ""))[:35] + "..."
            if len(str(getattr(m, a, ""))) > 35
            else str(getattr(m, a, ""))
        ),
        "revenue": lambda m, a: (
            f"{getattr(m, a, 0):,.2f} ₽" if getattr(m, a, 0) else "0 ₽"
        ),
        "is_my_company": lambda m, a: (
            "✅ Моя" if getattr(m, a, False) else "❌ Чужая"
        ),
    }

    # Форматтеры для детальной страницы
    column_formatters_detail: dict[str, Any] = {
        "title": lambda m, a: getattr(m, a, ""),
        "revenue": lambda m, a: (
            f"{getattr(m, a, 0):,.2f} ₽" if getattr(m, a, 0) else "0 ₽"
        ),
        "is_my_company": lambda m, a: (
            "✅ Моя компания" if getattr(m, a, False) else "❌ Не моя компания"
        ),
        "date_last_shipment": lambda m, a: (
            getattr(m, a, "").strftime(  # type: ignore[union-attr]
                "%d.%m.%Y %H:%M"
            )
            if getattr(m, a, "")
            else "Не указана"
        ),
    }

    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "title": "Название компании",
        "is_my_company": "Моя компания",
        "revenue": "Годовой оборот",
        "industry": "Сфера деятельности",
        "employees": "Численность сотрудников",
        "source": "Источник",
        "currency": "Валюта",
        "company_type": "Тип компании",
        "contact": "Контакт",
        "lead": "Лид",
        "main_activity": "Основная деятельность",
        "deal_failure_reason": "Причина провала",
        "deal_type": "Тип сделки",
        "shipping_company": "Фирма отгрузки",
        "banking_details": "Банковские реквизиты",
        "address_legal": "Юридический адрес",
        "address_company": "Адрес компании",
        "province_company": "Область/Край",
        "is_shipment_approved": "Разрешение на отгрузку",
        "date_last_shipment": "Дата последней отгрузки",
        "origin_version": "Версия данных",
        "parent_company": "Головная компания",
        "related_companies": "Дочерние компании",
        "deals": "Сделки",
        "leads": "Лиды",
        "contacts": "Контакты",
        "contracts": "Договоры",
        "invoices": "Счета",
        "delivery_notes": "Накладные",
        "position_head": "Должность руководителя",
        "basis_operates": "Основание деятельности",
        "position_head_genitive": "Должность руков. (род. падеж)",
        "basis_operates_genitive": "Основание деятельности (род. падеж)",
        "payment_delay_genitive": "Отсрочка (род. падеж)",
        "full_name_genitive": "ФИО (род. падеж)",
        "current_contract": "Текущий договор",
        "current_number_contract": "Номер договора",
    }

    column_default_sort = [("external_id", True)]

    column_sortable_list = [
        "external_id",
        "title",
        "revenue",
        "is_my_company",
        "date_last_shipment",
    ]

    column_searchable_list = [
        "external_id",
        "title",
        "address_legal",
        "address_company",
        "banking_details",
    ]

    form_columns = [  # Поля на форме редактирования
        "external_id",
        "title",
        "is_my_company",
        "revenue",
        "currency",
        "company_type",
        "industry",
        "employees",
        "source",
        "main_activity",
        "shipping_company",
        "banking_details",
        "address_legal",
        "address_company",
        "province_company",
        "is_shipment_approved",
        "parent_company",
    ]

    column_details_list = [  # Поля на форме просмотра
        "external_id",
        "title",
        "is_my_company",
        "revenue",
        "currency",
        "company_type",
        "industry",
        "employees",
        "source",
        "main_activity",
        "shipping_company",
        "banking_details",
        "address_legal",
        "address_company",
        "province_company",
        "is_shipment_approved",
        "date_last_shipment",
        "origin_version",
        "parent_company",
        "contact",
        "lead",
        "deal_failure_reason",
        "deal_type",
        "position_head",
        "basis_operates",
        "position_head_genitive",
        "basis_operates_genitive",
        "payment_delay_genitive",
        "full_name_genitive",
        "current_contract",
        "current_number_contract",
    ]
    """
    # Настройки AJAX для связанных полей
    form_ajax_refs = {
        "currency": {
            "fields": ("name", "symbol"),
            "order_by": "name",
        },
        "company_type": {
            "fields": ("name",),
            "order_by": "name",
        },
        "industry": {
            "fields": ("name",),
            "order_by": "name",
        },
        "employees": {
            "fields": ("name",),
            "order_by": "name",
        },
        "source": {
            "fields": ("name",),
            "order_by": "name",
        },
        "main_activity": {
            "fields": ("name",),
            "order_by": "name",
        },
        "shipping_company": {
            "fields": ("name",),
            "order_by": "name",
        },
        "parent_company": {
            "fields": ("title",),
            "order_by": "title",
        },
        "contact": {
            "fields": ["name", "last_name"]
        },
    }
    """
    # "currency": {
    #    "fields": ["name", "external_id"],
    #    "page_size": 10,
    #    "placeholder": "Search currency...",
    #    "minimum_input_length": 2
    # },

    """
    async def scaffold_form(
        self, rules: list[str] | None = None
    ) -> type[Form]:
        form_class = await super().scaffold_form(rules)
        default_render_kw = {
            "class": "form-control",  # Основной класс стилей
            "autocomplete": "off",  # Стандартный атрибут в SQLAdmin
            "spellcheck": "false",  # Отключение проверки орфографии
        }
        form_class.code_mark = StringField(
            "QR криптохвост",
            validators=[Optional()],
            render_kw=default_render_kw,
        )
        form_class.code_mark_mid = StringField(
            "QR сред", validators=[Optional()], render_kw=default_render_kw
        )
        form_class.doc_out = StringField(
            "Исходящий документ",
            validators=[Optional()],
            render_kw=default_render_kw,
        )
        return form_class  # type: ignore
    """
    icon = "fa-solid fa-building"


# Справочники
class DepartmentAdmin(BaseAdmin, model=Department):  # type: ignore[call-arg]
    name = "Отдел"
    name_plural = "Отделы"
    category = "Справочники"
    column_list = [  # Поля в списке
        "external_id",
        "name",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "name": "Название",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
    ]
    column_details_list = ["name", "id", "created_at"]  #
    icon = "fa-solid fa-tags"


class SourceAdmin(BaseAdmin, model=Source):  # type: ignore[call-arg]
    name = "Источник"
    name_plural = "Источники"
    category = "Источники"
    column_list = [  # Поля в списке
        "external_id",
        "name",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "name": "Название",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
    ]
    column_details_list = ["name", "id", "created_at"]  #
    icon = "fa-solid fa-chart-line"


class CreationSourceAdmin(
    BaseAdmin, model=CreationSource
):  # type: ignore[call-arg]
    name = "Сводные источники"
    name_plural = "Сводные источники"
    category = "Источники"
    column_list = [  # Поля в списке
        "external_id",
        "name",
        "ext_alt_id",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "name": "Название",
        "ext_alt_id": "id для связи со счётом",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
        "ext_alt_id",
    ]
    column_details_list = ["name", "id", "created_at"]  #
    icon = "fa-solid fa-arrow-right-arrow-left"


class DealTypeAdmin(BaseAdmin, model=DealType):  # type: ignore[call-arg]
    name = "Тип сделки"
    name_plural = "Типы сделок"
    category = "Источники"
    column_list = [  # Поля в списке
        "external_id",
        "name",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "name": "Название",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
    ]
    column_details_list = ["name", "id", "created_at"]  #
    icon = "fa-solid fa-tags"


class ShippingCompanyAdmin(
    BaseAdmin, model=ShippingCompany
):  # type: ignore[call-arg]
    name = "Фирма отгрузки"
    name_plural = "Фирмы отгрузки"
    category = "Справочники"

    column_list = [  # Поля в списке
        "external_id",
        "name",
        "ext_alt_id",
    ]
    column_labels = {  # Надписи полей в списке # type: ignore
        "external_id": "Внешний код",
        "name": "Название",
        "ext_alt_id": "Дополнительный код",
    }
    column_default_sort = [  # Сортировка по умолчанию # type: ignore
        ("external_id", True)
    ]
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
        "ext_alt_id",
    ]
    column_details_list = [
        "id",
        "name",
        "external_id",
        "ext_alt_id",
        "created_at",
    ]
    icon = "fa-solid fa-box"
    _is_base_class = False


class BillingAdmin(BaseAdmin, model=Billing):  # type: ignore[call-arg]
    name = "Платежка"
    name_plural = "Платёжки"
    category = "Бух документы"
    column_list = [  # Поля в списке
        "external_id",
        "name",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "name": "Название",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
    ]
    column_details_list = [
        "name",
        "id",
        "created_at",
        "payment_method",
        "amount",
        "date_payment",
        "number",
        "document_type",
        "invoice",
    ]  #
    icon = "fa-solid fa-money-check"


class DeliveryNoteAdmin(
    BaseAdmin, model=DeliveryNote
):  # type: ignore[call-arg]
    name = "Накладная"
    name_plural = "Накладные"
    category = "Бух документы"
    column_list = [  # Поля в списке
        "external_id",
        "name",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "name": "Название",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "name",
    ]
    column_details_list = ["name", "id", "created_at"]  #
    icon = "fa-solid fa-file-invoice"


class ManagerAdmin(BaseAdmin, model=Manager):  # type: ignore[call-arg]
    name = "Менеджер"
    name_plural = "Менеджеры"
    category = "Сотрудники"
    column_list = [  # Поля в списке
        "user_id",
        "is_active",
        "default_company_id",
    ]
    column_labels = {  # Надписи полей в списке
        "user_id": "Код пользователя",
        "is_active": "Менеджер активный",
        "default_company_id": "Компания по умолчанию",
    }
    column_default_sort = [("user_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "user_id",
        "is_active",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "user_id",
        "is_active",
        "default_company_id",
    ]
    form_columns = [
        "user",
        "is_active",
        "default_company",
    ]
    form_ajax_refs = {
        "user": {
            "fields": ("name",),
            "order_by": "name",
        },
        "default_company": {
            "fields": ("title",),
            "order_by": "title",
        },
    }
    column_details_list = [
        "user_id",
        "is_active",
        "default_company_id",
    ]  #
    icon = "fa-solid fa-id-card"

    """
    async def insert_model(
        self, request: Request, data: dict[str, Any]
    ) -> Any:
        # Обработка данных перед сохранением
        session: AsyncSession = get_session()
        if 'user_id' in data:
            # Преобразование external_id в id
            user = await session.get(User, data['user_id'])
            if user:
                data['user_id'] = user.id

        return await super().insert_model(request, data)
    """


class UserAdmin(BaseAdmin, model=User):  # type: ignore[call-arg]
    name = "Пользователь"
    name_plural = "Пользователи"
    category = "Сотрудники"
    column_list = [  # Поля в списке
        "external_id",
        "full_name",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Код пользователя",
        "full_name": "Имя",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "full_name",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "name",
        "full_name",
    ]
    form_columns = [
        "external_id",
        "full_name",
    ]
    # form_ajax_refs = {
    #    "user": {
    #        "fields": ("full_name",),
    #        "order_by": "username",
    #    },
    #    "default_company": {
    #        "fields": ("title",),
    #        "order_by": "title",
    #    }
    # }
    column_details_list = [
        "external_id",
        "full_name",
    ]  #
    icon = "fa-solid fa-user"


class TimelineCommentAdmin(
    BaseAdmin, model=TimelineComment
):  # type: ignore[call-arg]
    name = "Комментарий в ленте"
    name_plural = "Комментарии в ленте"
    category = "Доп справочники"
    column_list = [  # Поля в списке
        "external_id",
        "entity_id",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "entity_id": "Название",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "entity_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "entity_id",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "created",
        "entity_id",
        "entity_type",
        "author",
        "deal",
        "comment_entity",
    ]
    column_details_list = [
        "created",
        "entity_id",
        "entity_type",
        "author",
        "deal",
        "comment_entity",
    ]  #
    icon = "fa-solid fa-comment"


class AddInfoAdmin(BaseAdmin, model=AdditionalInfo):  # type: ignore[call-arg]
    name = "Доп информация сделки"
    name_plural = "Доп информации сделок"
    category = "Доп справочники"
    column_list = [  # Поля в списке
        "deal_id",
        "comment",
    ]
    column_labels = {  # Надписи полей в списке
        "deal_id": "ID сделки",
        "comment": "Дополнительная информация",
    }
    column_default_sort = [("deal_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "deal_id",
        "comment",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "deal_id",
        "comment",
    ]
    form_columns = [  # Поля на форме
        # "external_id",
        "comment",
        "deal",
    ]
    column_details_list = ["deal_id", "comment", "created_at"]  #
    icon = "fa-solid fa-note-sticky"


"""
class ContactAdmin(BaseAdmin):
    column_list = ["name", "last_name", "post", "company", "created_at"]
    form_columns = ["name", "last_name", "post", "company", "type"]
    column_searchable_list = ["name", "last_name"]
    icon = "fa-solid fa-user"


class LeadAdmin(BaseAdmin):
    column_list = ["title", "external_id", "status", "source", "created_at"]
    form_columns = ["title", "status", "source", "company", "contact"]
    icon = "fa-solid fa-funnel-dollar"


class InvoiceAdmin(BaseAdmin):
    column_list = [
        "title", "account_number", "opportunity", "invoice_stage", "created_at"
    ]
    form_columns = [
        "title", "account_number", "opportunity", "invoice_stage", "deal"
    ]
    icon = "fa-solid fa-file-invoice-dollar"


# Справочники
class CurrencyAdmin(NameIdAdmin):
    column_list = ["name", "external_id", "rate", "nominal"]
    form_columns = ["name", "external_id", "rate", "nominal"]
    icon = "fa-solid fa-money-bill-wave"


class CategoryAdmin(NameIdAdmin):
    icon = "fa-solid fa-tags"


class DealTypeAdmin(NameIdAdmin):
    icon = "fa-solid fa-diagram-project"


class SourceAdmin(NameIdAdmin):
    icon = "fa-solid fa-location-arrow"


# Пользователи
class UserAdmin(BaseAdmin):
    column_list = ["name", "last_name", "email", "work_position", "department"]
    form_columns = [
        "name", "last_name", "email", "work_position", "department"
    ]
    column_searchable_list = ["name", "last_name", "email"]
    icon = "fa-solid fa-users"


# Документы
class ContractAdmin(BaseAdmin):
    column_list = [
        "type_contract", "number_contract", "date_contract", "company"
    ]
    form_columns = [
        "type_contract", "number_contract", "date_contract", "company"
    ]
    icon = "fa-solid fa-file-contract"


class DeliveryNoteAdmin(BaseAdmin):
    column_list = ["opportunity", "company", "invoice", "paid_status"]
    column_formatters = {
        "paid_status": lambda m, a: m.paid_status
    }
    icon = "fa-solid fa-truck-loading"
"""


# Регистрация всех моделей
def register_models(admin: Admin) -> None:
    # Основные сущности
    admin.add_view(DealAdmin)
    admin.add_view(CompanyAdmin)
    admin.add_view(DepartmentAdmin)
    admin.add_view(SourceAdmin)
    admin.add_view(ShippingCompanyAdmin)
    admin.add_view(BillingAdmin)
    admin.add_view(DeliveryNoteAdmin)
    admin.add_view(TimelineCommentAdmin)
    admin.add_view(CreationSourceAdmin)
    admin.add_view(DealTypeAdmin)
    admin.add_view(ManagerAdmin)
    admin.add_view(AddInfoAdmin)
    admin.add_view(UserAdmin)
    """
    admin.add_view(ContactAdmin(Contact, name="Контакты"))
    admin.add_view(DealAdmin(Deal, name="Сделки"))
    admin.add_view(LeadAdmin(Lead, name="Лиды"))
    admin.add_view(InvoiceAdmin(Invoice, name="Счета"))

    # Справочники
    admin.add_view(CurrencyAdmin(Currency, name="Валюты"))
    admin.add_view(CategoryAdmin(Category, name="Категории"))
    admin.add_view(DealTypeAdmin(DealType, name="Типы сделок"))
    admin.add_view(SourceAdmin(Source, name="Источники"))
    admin.add_view(DealStageAdmin(DealStage, name="Стадии сделок"))
    admin.add_view(
        ShippingCompanyAdmin(ShippingCompany, name="Фирмы отгрузки")
    )

    # Пользователи
    admin.add_view(UserAdmin(User, name="Пользователи"))

    # Документы
    admin.add_view(ContractAdmin(Contract, name="Договоры"))
    admin.add_view(DeliveryNoteAdmin(DeliveryNote, name="Накладные"))
    admin.add_view(BillingAdmin(Billing, name="Платежи"))

    # Коммуникации
    admin.add_view(
        CommunicationChannelTypeAdmin(
            CommunicationChannelType, name="Типы каналов"
        )
    )
    admin.add_view(
        CommunicationChannelAdmin(CommunicationChannel, name="Каналы связи")
    )

    # Дополнительные справочники
    admin.add_view(MainActivityAdmin(MainActivity, name="Виды деятельности"))
    admin.add_view(IndustryAdmin(Industry, name="Отрасли"))
    admin.add_view(DefectTypeAdmin(DefectType, name="Виды дефектов"))
   """
