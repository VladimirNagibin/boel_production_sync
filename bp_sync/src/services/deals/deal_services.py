from datetime import datetime
from typing import Any

from fastapi import HTTPException

from core.logger import logger
from models.deal_models import Deal as DealDB
from schemas.company_schemas import CompanyCreate
from schemas.contact_schemas import ContactCreate
from schemas.deal_schemas import DealCreate, DealUpdate
from schemas.lead_schemas import LeadCreate
from schemas.product_schemas import EntityTypeAbbr, ListProductEntity

from ..base_services.base_service import BaseEntityClient
from ..products.product_bitrix_services import ProductBitrixClient
from ..timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from .deal_bitrix_services import DealBitrixClient
from .deal_repository import DealRepository
from .enums import CreationSourceEnum, DealSourceEnum, DealTypeEnum
from .handling_helpers import WEBSITE_CREATOR, identify_source
from .report_helpers import (
    create_dataframe,
    create_excel_file,
    process_deal_row_report,
)

BLACK_SYSTEM = 439


class DealClient(BaseEntityClient[DealDB, DealRepository, DealBitrixClient]):
    """Клиент для работы со сделками"""

    def __init__(
        self,
        deal_bitrix_client: DealBitrixClient,
        deal_repo: DealRepository,
        timeline_comments_bitrix_client: TimeLineCommentBitrixClient,
        product_bitrix_client: ProductBitrixClient,
    ):
        self._bitrix_client = deal_bitrix_client
        self._repo = deal_repo
        self.timeline_comments_bitrix_client = timeline_comments_bitrix_client
        self.product_bitrix_client = product_bitrix_client

    @property
    def entity_name(self) -> str:
        return "deal"

    @property
    def bitrix_client(self) -> DealBitrixClient:
        return self._bitrix_client

    @property
    def repo(self) -> DealRepository:
        return self._repo

    # deal report for the period
    async def _prepare_data_report(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Подготавливает данные для экспорта"""
        deals = await self.repo.fetch_deals(start_date, end_date)
        if not deals:
            logger.warning(f"No deals found for {start_date}-{end_date}")
            raise HTTPException(
                status_code=404, detail="No deals found in specified period"
            )

        return [await process_deal_row_report(deal) for deal in deals]

    async def export_deals_to_excel(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Основной метод экспорта сделок в Excel"""
        try:
            logger.info(
                f"Exporting deals to excel from {start_date} to {end_date}"
            )
            data = await self._prepare_data_report(start_date, end_date)
            df = await create_dataframe(data)
            return await create_excel_file(df)
        except Exception as e:
            logger.error(f"Export failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Export error: {str(e)}"
            ) from e

    # handling deal
    async def handler_deal(self, external_id: int) -> None:
        """Обработчик сделки"""
        try:
            self._cached_company: CompanyCreate | None = None
            self._cached_contact: ContactCreate | None = None
            self._cached_products: ListProductEntity | None = None
            deal_update = DealUpdate()
            deal_b24, deal_db, changes = await self.get_changes_b24_db(
                external_id
            )
            logger.debug(f"Changes detected for deal {external_id}: {changes}")
            needs_update = await self._check_source(
                deal_b24, deal_db, deal_update
            )
            products = (
                await self.product_bitrix_client.check_update_products_entity(
                    external_id, EntityTypeAbbr.DEAL
                )
            )
            self._cached_products = products
            if deal_db is None:  # not in database
                needs_update = (
                    await self._handle_new_deal(deal_b24, deal_update)
                    or needs_update
                )
            else:
                needs_update = (
                    await self._handle_exist_deal(
                        deal_b24, deal_db, deal_update
                    )
                    or needs_update
                )
            if needs_update:
                await self._synchronize_deal_data(
                    deal_b24, deal_db, deal_update
                )
        except Exception as e:
            logger.error(f"Error processing deal {external_id}: {str(e)}")
            raise
        finally:
            self._cached_company = None
            self._cached_contact = None
            self._cached_product = None

    async def _synchronize_deal_data(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        deal_update: DealUpdate,
    ) -> None:
        """Синхронизирует данные сделки между Bitrix24 и базой данных"""
        try:
            # Обновляем данные в Bitrix24
            await self.bitrix_client.update(deal_update)

            # Обновляем или создаем запись в базе данных
            if deal_db:
                await self.repo.update(deal_update)
            else:
                await self.repo.create(deal_b24)

            logger.info(
                f"Successfully synchronized deal {deal_b24.external_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to synchronize deal {deal_b24.external_id}: {str(e)}"
            )
            raise

    async def _handle_new_deal(
        self,
        deal_b24: DealCreate,
        deal_update: DealUpdate,
    ) -> bool:
        """Обработка новой сделки"""
        # TODO: Реализовать логику обработки новой сделки
        logger.info(f"Processing new deal: {deal_b24.external_id}")
        return True

    async def _handle_exist_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate,
        deal_update: DealUpdate,
    ) -> bool:
        """Обработка существующей сделки"""
        # TODO: Реализовать логику обработки существующей сделки
        logger.info(f"Processing existing deal: {deal_b24.external_id}")
        return True

    async def _check_source(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        deal_update: DealUpdate,
    ) -> bool:
        """Проверка и определение источника сделки"""
        try:
            needs_update = False
            creation_source_id = deal_b24.creation_source_id
            source_id = deal_b24.source_id
            type_id = deal_b24.type_id
            context: dict[str, Any] = {}
            result = await identify_source(
                deal_b24,
                self._get_lead,
                self._get_company,
                self._get_comments,
                context=context,
            )
            if "company" in context:
                self._cached_company = context["company"]
            creation_source_corr, type_correct, source_correct = result
            logger.info(
                f"{CreationSourceEnum.get_display_name(creation_source_corr)}"
                f":{creation_source_id}, "
                f"{DealTypeEnum.get_display_name(type_correct)}:{type_id}, "
                f"{DealSourceEnum.get_display_name(source_correct)}:"
                f"{source_id}"
            )

            if deal_db is None:  # new deal
                needs_update |= await self._update_field_if_needed(
                    deal_b24,
                    deal_update,
                    "creation_source_id",
                    creation_source_id,
                    creation_source_corr.value,
                )

                needs_update |= await self._update_field_if_needed(
                    deal_b24,
                    deal_update,
                    "source_id",
                    source_id,
                    source_correct.value,
                )

                needs_update |= await self._update_field_if_needed(
                    deal_b24,
                    deal_update,
                    "type_id",
                    type_id,
                    type_correct.value,
                )
                needs_update |= await self._handle_assignment(
                    deal_b24, deal_update, creation_source_corr
                )
                return needs_update
            # TODO: Реализовать логику обработки источников существующей сделки
            return needs_update
        except Exception as e:
            logger.error(
                f"Error identifying source for deal {deal_b24.external_id}: "
                f"{str(e)}"
            )
            raise

    async def _update_field_if_needed(
        self,
        deal_b24: DealCreate,
        deal_update: DealUpdate,
        field_name: str,
        current_value: Any,
        correct_value: Any,
    ) -> bool:
        """
        Обновляет поле сделки, если текущее значение отличается от корректного
        """
        if current_value != correct_value:
            setattr(deal_b24, field_name, correct_value)
            setattr(deal_update, field_name, correct_value)
            logger.info(
                f"Updated {field_name} from {current_value} to {correct_value}"
            )
            return True
        return False

    async def _handle_assignment(
        self,
        deal_b24: DealCreate,
        deal_update: DealUpdate,
        creation_source: CreationSourceEnum,
    ) -> bool:
        """
        Обрабатывает назначение ответственного в зависимости от источника
        сделки
        """
        needs_update = False

        if creation_source == CreationSourceEnum.AUTO:
            if deal_b24.assigned_by_id != WEBSITE_CREATOR:
                deal_b24.assigned_by_id = WEBSITE_CREATOR
                deal_update.assigned_by_id = WEBSITE_CREATOR
                needs_update = True
                logger.info(
                    "Assigned to website creator for auto-created deal"
                )
        else:
            if not await self._check_active_manager(deal_b24.assigned_by_id):
                deal_b24.assigned_by_id = WEBSITE_CREATOR
                deal_update.assigned_by_id = WEBSITE_CREATOR
                needs_update = True
                logger.info(
                    "Reassigned to website creator due to inactive manager"
                )

        return needs_update

    async def _get_lead(self, lead_id: int) -> LeadCreate | None:
        """Получение лида по ID"""
        try:
            lead_service = await self.repo.get_lead_client()
            return await lead_service.bitrix_client.get(lead_id)
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {str(e)}")
            return None

    async def _get_company(
        self,
        company_id: int,
    ) -> CompanyCreate | None:
        """Получение компании по ID"""
        try:
            company_service = await self.repo.get_company_client()
            return await company_service.bitrix_client.get(company_id)
        except Exception as e:
            logger.error(f"Failed to get company {company_id}: {str(e)}")
            return None

    async def _get_contact(
        self,
        contact_id: int,
    ) -> ContactCreate | None:
        """Получение контакта по ID"""
        try:
            contact_service = await self.repo.get_contact_client()
            return await contact_service.bitrix_client.get(contact_id)
        except Exception as e:
            logger.error(f"Failed to get contact {contact_id}: {str(e)}")
            return None

    async def _get_comments(
        self,
        deal_id: int,
    ) -> str:
        try:
            timeline_client = self.timeline_comments_bitrix_client
            comments_result = await timeline_client.get_comments_by_entity(
                "deal", deal_id
            )
            comments: list[str] = [
                comm.comment_entity
                for comm in comments_result.result
                if comm.comment_entity
            ]
            return "; ".join(comments)
        except Exception as e:
            logger.error(f"Failed to get comments deal {deal_id}: {str(e)}")
            return ""

    async def _check_active_manager(self, manager_id: int) -> bool:
        """Проверка активных менеджеров"""
        try:
            user_service = await self.repo.get_user_client()
            return await user_service.repo.is_activity_manager(manager_id)
        except Exception as e:
            logger.error(f"Failed to check manager {manager_id}: {str(e)}")
            return False

    async def _check_available_stage(self, deal_b24: DealCreate) -> int:
        """
        Определяет доступную стадию сделки на основе заполненных данных.

        Стадии:
        1 - базовая стадия
        2 - заполнены контактные данные (компания или контакт)
        3 - заполнены товары, основная деятельность и город
        4 - заполнены компания покупателя и фирма отгрузки
        5 - наличие договора с компанией по фирме отгрузки

        Args:
            deal_b24: Данные сделки

        Returns:
            Номер доступной стадии (1-4)
        """
        # Стадия 1: Базовая стадия
        available_stage = 1

        # Проверяем условия для перехода на стадию 2
        if await self._has_contact_details(deal_b24):
            available_stage = 2
        else:
            return available_stage

        # Проверяем условия для перехода на стадию 3
        if not await self._has_required_stage3_data(deal_b24):
            return available_stage

        available_stage = 3

        # Проверяем условия для перехода на стадию 4
        if not await self._has_required_stage4_data(deal_b24):
            return available_stage

        available_stage = 4

        # Проверяем условия для перехода на стадию 5
        if await self._has_required_stage5_data(deal_b24):
            available_stage = 5

        return available_stage

    async def _has_contact_details(self, deal_b24: DealCreate) -> bool:
        """
        Проверяет наличие контактных данных (email или телефон)
        в компании или контакте.
        """
        # Получаем данные компании
        company = await self._get_company_data(deal_b24)

        # Проверяем контактные данные компании
        if company and (company.has_email or company.has_phone):
            return True

        # Проверяем контактные данные контакта
        contact = await self._get_contact_data(deal_b24)
        if contact and (contact.has_email or contact.has_phone):
            return True

        return False

    async def _get_company_data(
        self, deal_b24: DealCreate
    ) -> CompanyCreate | None:
        """
        Получает данные компании из кэша или запрашивает при необходимости.
        """
        if self._cached_company:
            return self._cached_company

        if deal_b24.company_id:
            company = await self._get_company(deal_b24.company_id)
            if company:
                self._cached_company = company
                return company

        return None

    async def _get_contact_data(
        self, deal_b24: DealCreate
    ) -> ContactCreate | None:
        """
        Получает данные контакта из кэша или запрашивает при необходимости.
        """
        if self._cached_contact:
            return self._cached_contact

        if deal_b24.contact_id:
            contact = await self._get_contact(deal_b24.contact_id)
            if contact:
                self._cached_contact = contact
                return contact

        return None

    async def _has_required_stage3_data(self, deal_b24: DealCreate) -> bool:
        """
        Проверяет наличие данных для перехода на стадию 3:
        - Товары
        - Основная деятельность клиента
        - Город клиента
        """
        # Проверяем наличие товаров
        if not (
            self._cached_products and self._cached_products.count_products > 0
        ):
            return False

        # Получаем данные компании
        company = await self._get_company_data(deal_b24)

        # Проверяем основную деятельность
        if (
            (not deal_b24.main_activity_id)
            and company
            and company.main_activity_id
        ):
            deal_b24.main_activity_id = company.main_activity_id
            # TODO: добавить флаг обновления и обновить deal_update
        if not (
            deal_b24.main_activity_id or (company and company.main_activity_id)
        ):
            return False

        # Проверяем город
        if not deal_b24.city and company and company.city:
            deal_b24.city = company.city
            # TODO: добавить флаг обновления и обновить deal_update
        if not deal_b24.city and not (company and company.city):
            return False

        return True

    async def _has_required_stage4_data(self, deal_b24: DealCreate) -> bool:
        """
        Проверяет наличие данных для перехода на стадию 4:
        - Компания покупателя
        - Фирма отгрузки
        """
        # Получаем данные компании
        company = await self._get_company_data(deal_b24)

        if not company:
            contact = await self._get_contact_data(deal_b24)
            if contact and contact.company_id:
                company = await self._get_company(contact.company_id)
                if company:
                    deal_b24.company_id = contact.company_id
                    # TODO: добавить флаг обновления и обновить deal_update
                    self._cached_company = company

        if (
            (not company)
            and deal_b24.shipping_company_id
            and deal_b24.shipping_company_id == BLACK_SYSTEM
        ):
            company_id = await self._get_default_company(
                deal_b24.assigned_by_id
            )
            if company_id:
                company = await self._get_company(company_id)
            if company:
                deal_b24.company_id = company_id
                if self._cached_contact:
                    await self._add_contact_comment(
                        self._cached_contact, deal_b24
                    )
                # TODO: добавить флаг обновления и обновить deal_update
                self._cached_company = company

        # Проверяем наличие компании и фирмы отгрузки
        return bool(company and deal_b24.shipping_company_id)

    async def _has_required_stage5_data(self, deal_b24: DealCreate) -> bool:
        """
        Проверяет наличие данных для перехода на стадию 5:
        - наличие договора с компанией по фирме отгрузки
        - обработка разных фирм отгрузки
        """
        # company = self._cached_company
        # shipping_company_id = deal_b24.shipping_company_id
        # TODO: реализовать проверку наличие договора
        return True

    async def _get_default_company(self, user_id: int) -> int | None:
        try:
            user_service = await self.repo.get_user_client()
            return await user_service.repo.get_default_company_manager(user_id)
        except Exception as e:
            logger.error(
                f"Failed to get default company manager {user_id}: {str(e)}"
            )
            return None

    async def _add_contact_comment(
        self, contact: ContactCreate, deal_b24: DealCreate
    ) -> None:
        comment = await self._get_contact_comment(contact)
        if comment:
            await self._update_comment(comment, deal_b24)

    async def _update_comment(
        self, comment: str, deal_b24: DealCreate
    ) -> bool:
        comments_deal = deal_b24.comments
        if not comments_deal:
            deal_b24.comments = comment
            # TODO: добавить флаг обновления и обновить deal_update
            return True
        if comment in comments_deal:
            return False
        deal_b24.comments = (
            f"<div>{comments_deal}</div><div>{comment}<br></div>"
        )
        # TODO: добавить флаг обновления и обновить deal_update
        return True

    async def _get_contact_comment(self, contact: ContactCreate) -> str | None:
        phone_values: list[str] = []
        email_values: list[str] = []
        if contact.has_phone:
            phones = contact.phone
            if phones:
                for phone in phones:
                    phone_values.append(phone.value)
        if contact.has_email:
            emails = contact.email
            if emails:
                for email in emails:
                    email_values.append(email.value)
        phone_str = (
            f"<div>Телефон {', '.join(phone_values)}<br></div>"
            if phone_values
            else ""
        )
        email_str = (
            f"<div>E-mail {', '.join(email_values)}<br></div>"
            if email_values
            else ""
        )
        if phone_str or email_str:
            return f"{phone_str}{email_str}"
        return None
