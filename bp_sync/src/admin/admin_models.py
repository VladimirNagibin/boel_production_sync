# from typing import Any

from sqladmin import Admin, ModelView

from models.communications import (  # noqa: F401
    CommunicationChannel,
    CommunicationChannelType,
)
from models.company_models import Company  # noqa: F401
from models.contact_models import Contact  # noqa: F401
from models.deal_documents import Billing, Contract  # noqa: F401
from models.deal_models import Deal  # noqa: F401
from models.delivery_note_models import DeliveryNote  # noqa: F401
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
from models.user_models import User  # noqa: F401

# from wtforms import Form, StringField
# from wtforms.validators import Optional


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
    column_list = [  # Поля в списке
        "external_id",
        "title",
        "opportunity",
        "begindate",
    ]
    column_labels = {  # Надписи полей в списке
        "external_id": "Внешний код",
        "title": "Название",
        "opportunity": "Сумма",
        "begindate": "Дата начала",
    }
    column_default_sort = [("external_id", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "external_id",
        "title",
        "opportunity",
        "begindate",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "title",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "external_id",
        "title",
        "opportunity",
        "begindate",
        "closedate",
        "stage_id",
        "category_id",
    ]
    column_details_list = ["title", "stage_semantic_id", "payment_type"]  #
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
    column_list = [  # Поля в списке
        "title",
        "external_id",
        "revenue",
        "city",
        "created_at",
    ]
    column_labels = {  # Надписи полей в списке
        "title": "Название",
        "external_id": "Код Б24",
        "revenue": "Оборот за год",
    }
    column_default_sort = [("title", True)]  # Сортировка по умолчанию
    column_sortable_list = [  # Список полей по которым возможна сортировка
        "title",
        "external_id",
    ]
    column_searchable_list = [  # Список полей по которым возможен поиск
        "title",
        "external_id",
    ]
    form_columns = [  # Поля на форме
        "title",
        "revenue",
        "currency",
        "company_type",
        "contact",
    ]
    column_details_list = ["title", "address_legal", "banking_details"]  #
    form_ajax_refs = {  # Поиск поля по значению из списка
        # "currency": {
        #    "fields": ["name", "external_id"],
        #    "page_size": 10,
        #    "placeholder": "Search currency...",
        #    "minimum_input_length": 2
        # },
        "company_type": {"fields": ["name"]},
        "contact": {"fields": ["name", "last_name"]},
    }
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
    icon = "fa-solid fa-location-arrow"


class CreationSourceAdmin(
    BaseAdmin, model=CreationSource
):  # type: ignore[call-arg]
    name = "Сводные источники"
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
    icon = "fa-solid fa-location-arrow"


class DealTypeAdmin(BaseAdmin, model=DealType):  # type: ignore[call-arg]
    name = "Тип сделки"
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
    icon = "fa-solid fa-location-arrow"


class ShippingCompanyAdmin(
    BaseAdmin, model=ShippingCompany
):  # type: ignore[call-arg]
    name = "Фирмы отгрузки"
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
    icon = "fa-solid fa-location-arrow"


class BillingAdmin(BaseAdmin, model=Billing):  # type: ignore[call-arg]
    name = "Платежи"
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
    icon = "fa-solid fa-location-arrow"


class DeliveryNoteAdmin(
    BaseAdmin, model=DeliveryNote
):  # type: ignore[call-arg]
    name = "Накладные"
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
    icon = "fa-solid fa-location-arrow"


class TimelineCommentAdmin(
    BaseAdmin, model=TimelineComment
):  # type: ignore[call-arg]
    name = "Комментарии"
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
    icon = "fa-solid fa-location-arrow"


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
