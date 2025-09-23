from datetime import datetime

from pydantic import Field, field_validator

from .base_schemas import (
    SYSTEM_USER_ID,
    AddressMixin,
    BaseCreateSchema,
    BaseUpdateSchema,
    CommunicationChannel,
    HasCommunicationCreateMixin,
    HasCommunicationUpdateMixin,
)


class BaseContact:
    """
    Общие поля создания и обновления с алиасами для соответствия
    SQLAlchemy модели
    """

    # Идентификаторы и основные данные
    name: str | None = Field(None, alias="NAME")
    second_name: str | None = Field(None, alias="SECOND_NAME")
    last_name: str | None = Field(None, alias="LAST_NAME")
    post: str | None = Field(None, alias="POST")

    # Статусы и флаги
    export: bool | None = Field(None, alias="EXPORT")
    is_shipment_approved: bool | None = Field(
        None, alias="UF_CRM_60D97EF75E465"
    )

    # Временные метки
    birthdate: datetime | None = Field(None, alias="BIRTHDATE")

    # География и источники
    city: str | None = Field(None, alias="UF_CRM_DCT_CITY")
    source_external: str | None = Field(None, alias="UF_CRM_DCT_SOURCE")
    origin_version: str | None = Field(None, alias="ORIGIN_VERSION")

    # Связи с другими сущностями
    type_id: str | None = Field(None, alias="TYPE_ID")
    company_id: int | None = Field(None, alias="COMPANY_ID")
    lead_id: int | None = Field(None, alias="LEAD_ID")
    source_id: str | None = Field(None, alias="SOURCE_ID")
    main_activity_id: int | None = Field(None, alias="UF_CRM_1598882745")
    deal_failure_reason_id: int | None = Field(
        None, alias="UF_CRM_6539DA9518373"
    )
    deal_type_id: str | None = Field(None, alias="UF_CRM_61236340EA7AC")

    # Маркетинговые метки
    mgo_cc_entry_id: str | None = Field(None, alias="UF_CRM_63E1D6D4B8A68")
    mgo_cc_channel_type: str | None = Field(None, alias="UF_CRM_63E1D6D4C89EA")
    mgo_cc_result: str | None = Field(None, alias="UF_CRM_63E1D6D4D40E8")
    mgo_cc_entry_point: str | None = Field(None, alias="UF_CRM_63E1D6D4DFC93")
    mgo_cc_create: datetime | None = Field(None, alias="UF_CRM_63E1D6D4EC444")
    mgo_cc_end: datetime | None = Field(None, alias="UF_CRM_63E1D6D5051DE")
    mgo_cc_tag_id: str | None = Field(None, alias="UF_CRM_63E1D6D515198")
    calltouch_site_id: str | None = Field(None, alias="UF_CRM_CALLTOUCHWWLX")
    calltouch_call_id: str | None = Field(None, alias="UF_CRM_CALLTOUCHZLRD")
    calltouch_request_id: str | None = Field(
        None, alias="UF_CRM_CALLTOUCHZGWC"
    )

    # Социальные профили
    wz_instagram: str | None = Field(None, alias="UF_CRM_INSTAGRAM_WZ")
    wz_vc: str | None = Field(None, alias="UF_CRM_VK_WZ")
    wz_telegram_username: str | None = Field(
        None, alias="UF_CRM_TELEGRAMUSERNAME_WZ"
    )
    wz_telegram_id: str | None = Field(None, alias="UF_CRM_TELEGRAMID_WZ")
    wz_avito: str | None = Field(None, alias="UF_CRM_AVITO_WZ")

    # Коммуникации
    phone: list[CommunicationChannel] | None = Field(None, alias="PHONE")
    email: list[CommunicationChannel] | None = Field(None, alias="EMAIL")
    web: list[CommunicationChannel] | None = Field(None, alias="WEB")
    im: list[CommunicationChannel] | None = Field(None, alias="IM")
    link: list[CommunicationChannel] | None = Field(None, alias="LINK")

    # Дополнительные ответственные
    additional_responsible: list[int] | None = Field(
        None, alias="UF_CRM_1629106625"
    )

    @field_validator("external_id", mode="before")  # type: ignore[misc]
    @classmethod
    def convert_str_to_int(cls, value: str | int) -> int:
        """Автоматическое преобразование строк в числа для ID"""
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value  # type: ignore[return-value]


class ContactCreate(
    BaseCreateSchema, BaseContact, AddressMixin, HasCommunicationCreateMixin
):
    """Модель для создания контактов"""

    @classmethod
    def get_default_entity(cls, external_id: int) -> "ContactCreate":
        now = datetime.now()
        return ContactCreate(
            # Обязательные поля из TimestampsCreateMixin
            date_create=now,
            date_modify=now,
            # Обязательные поля из UserRelationsCreateMixin
            assigned_by_id=SYSTEM_USER_ID,  # SYSTEM_USER_ID
            created_by_id=SYSTEM_USER_ID,  # SYSTEM_USER_ID
            modify_by_id=SYSTEM_USER_ID,  # SYSTEM_USER_ID
            # Обязательные поля из HasCommunicationCreateMixin
            has_phone=False,
            has_email=False,
            has_imol=False,
            name=f"Deleted Contact {external_id}",
            # Задаем external_id и флаг удаления
            external_id=external_id,  # Ваш внешний ID
            is_deleted_in_bitrix=True,
            # created_at=now,
            # updated_at=now,
        )


class ContactUpdate(
    BaseUpdateSchema, BaseContact, AddressMixin, HasCommunicationUpdateMixin
):
    """Модель для частичного обновления контактов"""

    ...
