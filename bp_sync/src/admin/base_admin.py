from sqladmin import ModelView


# Базовые модели
class BaseAdmin(ModelView):  # type: ignore[misc]
    page_size = 50
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    can_view_details = True
    icon = "fa-solid fa-table"
