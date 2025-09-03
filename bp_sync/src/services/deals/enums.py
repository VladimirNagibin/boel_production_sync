from enum import IntEnum, StrEnum

EXCLUDE_FIELDS_FOR_COMPARE = {
    "internal_id",
    "created_at",
    "updated_at",
    "is_deleted_in_bitrix",
    "parent_deal_id",
    "is_frozen",
    "is_setting_source",
}


class CreationSourceEnum(IntEnum):
    AUTO = 805  # авто
    MANUAL = 807  # ручной

    @classmethod
    def get_display_name(cls, value: int) -> str:
        """Get display name by value"""
        display_names = {
            805: "авто",
            807: "ручной",
        }
        return display_names.get(value, "Неизвестно")

    @classmethod
    def from_value(cls, value: int | None) -> "CreationSourceEnum":
        """Get enum member by value"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value {value}")


class DealTypeEnum(StrEnum):
    DIRECT_SALES = "1"  # Прямые продажи
    MARKETPLACE = "4"  # Маркетплейс
    ONLINE_SALES = "5"  # Интернет продажа
    FOREIGN_TRADE = "7"  # ВЭД

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """Get display name by value"""
        display_names = {
            "1": "Прямые продажи",
            "4": "Маркетплейс",
            "5": "Интернет продажа",
            "7": "ВЭД",
        }
        return display_names.get(value, "Неизвестно")

    @classmethod
    def from_value(cls, value: str | None) -> "DealTypeEnum":
        """Get enum member by value"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value {value}")


class DealSourceEnum(StrEnum):
    EXISTING_CLIENT = "PARTNER"  # Существующий клиент
    NEW_CLIENT = "19"  # Новый клиент
    CALL = "CALL"  # Звонок
    WEBSITE_BOELSHOP = "WEB"  # Веб-сайт BOELSHOP
    ORDER_BOELSHOP = "21"  # Заказ BOELSHOP
    CALL_BOELSHOP = "22"  # Звонок BOELSHOP
    CRM_FORM = "WEBFORM"  # CRM-форма
    VYBEERAI = "20"  # Выбирай
    EMAIL = "23"  # EMAIL

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """Get display name by value"""
        display_names = {
            "PARTNER": "Существующий клиент",
            "19": "Новый клиент",
            "CALL": "Звонок",
            "WEB": "Веб-сайт BOELSHOP",
            "21": "Заказ BOELSHOP",
            "22": "Звонок BOELSHOP",
            "WEBFORM": "CRM-форма",
            "20": "Выбирай",
            "23": "EMAIL",
        }
        return display_names.get(value, "Неизвестно")

    @classmethod
    def from_value(cls, value: str | None) -> "DealSourceEnum":
        """Get enum member by value"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"No matching enum member for value {value}")
