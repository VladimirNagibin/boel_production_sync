from typing import Any


class AdminListAndDetailMixin:
    column_default_sort = [("external_id", True)]

    @staticmethod
    def format_title(model: Any, attribute: str) -> str:
        title = str(getattr(model, attribute, ""))
        return title[:35] + "..." if len(title) > 35 else title

    @staticmethod
    def format_currency(
        model: Any, attribute: str, currency_symbol: str = ""
    ) -> str:
        value = getattr(model, attribute, 0)
        return (
            f"{value:,.2f} {currency_symbol}".strip()
            if value
            else f"0 {currency_symbol}".strip()
        )

    @staticmethod
    def format_enum_display(
        enum_class: Any, model: Any, attribute: str
    ) -> str:
        """Форматирование enum значений для отображения"""
        value = getattr(model, attribute, "")
        return enum_class.get_display_name(value) if value else "Не указано"

    @staticmethod
    def format_opportunity(model: Any, attribute: str) -> str:
        """Форматирование суммы"""
        value = getattr(model, attribute, 0)
        return f"{value:,.2f}" if value else "0"

    @staticmethod
    def format_date(model: Any, attribute: str) -> str:
        """Форматирование даты"""
        value = getattr(model, attribute, None)
        return value.strftime("%d.%m.%Y") if value else "-"
