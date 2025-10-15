from typing import Type

from sqladmin import Admin
from wtforms import Form

# from .mixins import AdminListAndDetailMixin
from models.communications import (  # noqa: F401
    CommunicationChannel,
    CommunicationChannelType,
)
from models.contact_models import Contact  # noqa: F401
from models.deal_documents import Billing, Contract  # noqa: F401
from models.deal_models import AdditionalInfo  # noqa: F401
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
from models.user_models import Manager, User  # noqa: F401

from .base_admin import BaseAdmin
from .company_admin_model import CompanyAdmin
from .contact_admin_model import ContactAdmin
from .deal_admin_model import DealAdmin
from .deal_export_admin import DealExportAdmin
from .invoice_admin_model import InvoiceAdmin

# from wtforms import Form, StringField
# from wtforms.validators import Optional
# from sqlalchemy.ext.asyncio import AsyncSession
# from db.postgres import get_session


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
    icon = "fa-solid fa-id-card"

    column_list = [  # Поля в списке
        "user_id",
        "user",
        "is_active",
        "default_company_id",
        "default_company",
        "disk_id",
    ]
    column_labels = {  # Надписи полей в списке
        "user_id": "Код пользователя",
        "user": "Пользователь",
        "is_active": "Менеджер активный",
        "default_company_id": "Код компании по умолчанию",
        "default_company": "Компания по умолчанию",
        "disk_id": "Код диска",
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
        "user_id",
        "is_active",
        "default_company_id",
        "disk_id",
    ]

    # Переопределяем форму
    form_include_pk = True

    async def get_form(self) -> Type[Form]:
        Form_class = await super().get_form()

        # Получаем список компаний для выпадающего списка
        # async with self.session_maker(expire_on_commit=False) as session:
        #    result = await session.execute(select(Company))
        #    companies = result.scalars().all()
        #    choices = [(c.external_id, str(c)) for c in companies]

        # Динамически добавляем choices к полю default_company_id
        Form_class.default_company_id.kwargs["choices"] = []  # choices
        Form_class.default_company_id.kwargs["coerce"] = int
        Form_class.user_id.kwargs["choices"] = []  # choices
        Form_class.user_id.kwargs["coerce"] = int
        return Form_class  # type: ignore

    # form_ajax_refs = {
    #    "user": {
    #        "fields": ("name",),
    #        "order_by": "name",
    #    },
    #    "default_company": {
    #        "fields": ("title","external_id"),
    #        "order_by": "title",
    #    },
    # }

    column_details_list = [
        "user_id",
        "user",
        "is_active",
        "default_company_id",
        "default_company",
        "disk_id",
    ]

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
        # "full_name",
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


class ContractAdmin(BaseAdmin, model=Contract):  # type: ignore[call-arg]
    name = "Договор"
    name_plural = "Договора"
    category = "Бух документы"
    column_list = [
        "shipping_company",
        "company",
        "number_contract",
        "date_contract",
        "type_contract",
        "is_deleted_in_bitrix",
        "period_contract",
    ]
    form_columns = [
        "type_contract",
        "number_contract",
        "date_contract",
        "company",
    ]
    icon = "fa-solid fa-file-contract"


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
    admin.add_view(DealExportAdmin)
    admin.add_view(ContractAdmin)
    admin.add_view(ContactAdmin)
    admin.add_view(InvoiceAdmin)

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
