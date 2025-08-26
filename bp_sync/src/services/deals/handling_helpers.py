from typing import Awaitable, Callable

from core.logger import logger
from schemas.company_schemas import CompanyCreate
from schemas.deal_schemas import DealCreate
from schemas.lead_schemas import LeadCreate

from .enums import CreationSourceEnum, DealSourceEnum, DealTypeEnum

WEBSITE_CREATOR = 5095
FOREIGN_ASSIGNED = 9023
DAYS_THRESHOLD_FOR_EXISTING_CLIENT = 14

GetLeadFunc = Callable[[int], Awaitable[LeadCreate | None]]
GetCompanyFunc = Callable[[int], Awaitable[CompanyCreate | None]]
GetCommentsFunc = Callable[[int], Awaitable[str]]


async def identify_source(
    deal_b24: DealCreate,
    get_lead: GetLeadFunc | None = None,
    get_company: GetCompanyFunc | None = None,
    get_comments: GetCommentsFunc | None = None,
    lead: LeadCreate | None = None,
    company: CompanyCreate | None = None,
    comments_: str | None = None,
) -> tuple[CreationSourceEnum, DealTypeEnum, DealSourceEnum]:
    """
    Определяет источник, тип и канал сделки на основе различных критериев

    Args:
        deal_b24: Данные сделки из Bitrix24
        get_lead: Функция для получения лида (опционально)
        get_company: Функция для получения компании (опционально)
        get_comments: Функция для получения комментариев (опционально)
        lead: Данные лида (опционально)
        company: Данные компании (опционально)
        comments_: Комментарии к сделке (опционально)

    Returns:
        Кортеж с определенным источником создания, типом сделки и
        источником сделки

    Raises:
        ValueError: Если не предоставлены необходимые данные для определения
        источника
    """
    # Определяем базовый тип сделки
    deal_type = _get_base_deal_type(deal_b24)

    # Получаем данные лида, если они не предоставлены напрямую
    lead_data = await _get_lead_data(deal_b24, get_lead, lead)

    # Если есть данные лида, анализируем их
    if lead_data:
        return await _identify_source_from_lead(
            deal_b24,
            deal_type,
            lead_data,
            get_company,
            get_comments,
            company,
            comments_,
        )

    # Если лида нет, используем стандартную логику
    return await _identify_source_without_lead(
        deal_b24, deal_type, get_company, company
    )


def _get_base_deal_type(deal_b24: DealCreate) -> DealTypeEnum:
    """Определяет базовый тип сделки на основе ответственного"""
    if deal_b24.assigned_by_id == FOREIGN_ASSIGNED:
        return DealTypeEnum.FOREIGN_TRADE
    return DealTypeEnum.DIRECT_SALES


async def _get_lead_data(
    deal_b24: DealCreate,
    get_lead: GetLeadFunc | None,
    lead: LeadCreate | None,
) -> LeadCreate | None:
    """Получает данные лида из доступных источников"""
    if lead is not None:
        return lead

    if get_lead is not None and deal_b24.lead_id is not None:
        return await get_lead(deal_b24.lead_id)

    return None


async def _identify_source_from_lead(
    deal_b24: DealCreate,
    base_deal_type: DealTypeEnum,
    lead: LeadCreate,
    get_company: GetCompanyFunc | None = None,
    get_comments: GetCommentsFunc | None = None,
    company: CompanyCreate | None = None,
    comments_: str | None = None,
) -> tuple[CreationSourceEnum, DealTypeEnum, DealSourceEnum]:
    """Определяет источник сделки на основе данных лида"""
    title_lead = lead.title

    # Проверяем различные условия для определения источника
    if "Выбирай" in title_lead:
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.MARKETPLACE
            ),
            DealSourceEnum.VYBEERAI,
        )

    if lead.source_id == "WEBFORM":
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.CRM_FORM,
        )

    if "Лид BOELSHOP #" in title_lead:
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.ORDER_BOELSHOP,
        )

    # Проверяем CallTouch данные
    if deal_b24.calltouch_site_id or lead.calltouch_call_id:
        return _identify_calltouch_source(title_lead, base_deal_type)

    # Проверяем другие условия
    if "Входящий звонок" in title_lead:
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.CALL,
        )

    if deal_b24.origin_id:
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.EMAIL,
        )

    if deal_b24.created_by_id == WEBSITE_CREATOR:
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.WEBSITE_BOELSHOP,
        )

    if "Чат BOELSHOP.ru" in title_lead:
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.WEBSITE_BOELSHOP,
        )

    # Проверяем комментарии на наличие UTM-меток
    comments_data = await _get_comments_data(deal_b24, get_comments, comments_)
    if "utm_source" in comments_data:
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.WEBSITE_BOELSHOP,
        )

    # Если не подошли другие условия, проверяем компанию
    return await _identify_company_source(
        deal_b24, base_deal_type, get_company, company
    )


def _identify_calltouch_source(
    lead_title: str, base_deal_type: DealTypeEnum
) -> tuple[CreationSourceEnum, DealTypeEnum, DealSourceEnum]:
    """Определяет источник на основе данных CallTouch"""
    if "звонок" in lead_title.lower():
        return (
            CreationSourceEnum.AUTO,
            (
                base_deal_type
                if base_deal_type == DealTypeEnum.FOREIGN_TRADE
                else DealTypeEnum.ONLINE_SALES
            ),
            DealSourceEnum.CALL_BOELSHOP,
        )
    return (
        CreationSourceEnum.AUTO,
        (
            base_deal_type
            if base_deal_type == DealTypeEnum.FOREIGN_TRADE
            else DealTypeEnum.ONLINE_SALES
        ),
        DealSourceEnum.WEBSITE_BOELSHOP,
    )


async def _get_comments_data(
    deal_b24: DealCreate,
    get_comments: GetCommentsFunc | None,
    comments_: str | None,
) -> str:
    """Получает комментарии из доступных источников"""
    if comments_ is not None:
        return comments_

    if get_comments is not None:
        # Преобразуем external_id к нужному типу
        external_id = deal_b24.external_id

        # Проверяем тип external_id и преобразуем при необходимости
        if isinstance(external_id, int):
            # Если это число, используем как есть
            return await get_comments(external_id)
        elif isinstance(external_id, str) and external_id.isdigit():
            # Если это строка, содержащая число, преобразуем
            return await get_comments(int(external_id))
        else:
            # Если тип не поддерживается, логируем ошибку и возвращаем пустую
            logger.warning(
                f"Неверный тип external_id: {type(external_id)}. "
                f"Ожидается int или строка с цифрами."
            )
            return ""

    return ""


async def _identify_company_source(
    deal_b24: DealCreate,
    base_deal_type: DealTypeEnum,
    get_company: GetCompanyFunc | None,
    company: CompanyCreate | None,
) -> tuple[CreationSourceEnum, DealTypeEnum, DealSourceEnum]:
    """Определяет источник сделки на основе данных компании"""
    company_data = await _get_company_data(deal_b24, get_company, company)

    if not company_data:
        return (
            CreationSourceEnum.MANUAL,
            base_deal_type,
            DealSourceEnum.NEW_CLIENT,
        )

    # Проверяем, является ли клиент существующим
    if await _is_existing_client(company_data, deal_b24):
        return (
            CreationSourceEnum.MANUAL,
            base_deal_type,
            DealSourceEnum.EXISTING_CLIENT,
        )

    return (
        CreationSourceEnum.MANUAL,
        base_deal_type,
        DealSourceEnum.NEW_CLIENT,
    )


async def _get_company_data(
    deal_b24: DealCreate,
    get_company: GetCompanyFunc | None = None,
    company: CompanyCreate | None = None,
) -> CompanyCreate | None:
    """Получает данные компании из доступных источников"""
    if company is not None:
        return company

    if get_company is not None and deal_b24.company_id is not None:
        return await get_company(deal_b24.company_id)

    return None


async def _is_existing_client(
    company: CompanyCreate, deal_b24: DealCreate
) -> bool:
    """Проверяет, является ли клиент существующим"""
    try:
        if not company.date_create or not deal_b24.date_create:
            return False

        time_difference = deal_b24.date_create - company.date_create
        return time_difference.days > DAYS_THRESHOLD_FOR_EXISTING_CLIENT
    except (TypeError, AttributeError):
        return False


async def _identify_source_without_lead(
    deal_b24: DealCreate,
    base_deal_type: DealTypeEnum,
    get_company: GetCompanyFunc | None = None,
    company: CompanyCreate | None = None,
) -> tuple[CreationSourceEnum, DealTypeEnum, DealSourceEnum]:
    """Определяет источник для сделки без привязанного лида"""
    company_data = await _get_company_data(deal_b24, get_company, company)

    if not company_data:
        return (
            CreationSourceEnum.MANUAL,
            base_deal_type,
            DealSourceEnum.NEW_CLIENT,
        )

    if await _is_existing_client(company_data, deal_b24):
        return (
            CreationSourceEnum.MANUAL,
            base_deal_type,
            DealSourceEnum.EXISTING_CLIENT,
        )

    return (
        CreationSourceEnum.MANUAL,
        base_deal_type,
        DealSourceEnum.NEW_CLIENT,
    )
