from datetime import datetime
from typing import Any

from fastapi import HTTPException, status

from core.logger import logger
from models.deal_models import Deal as DealDB
from models.enums import StageSemanticEnum
from schemas.company_schemas import CompanyCreate
from schemas.contact_schemas import ContactCreate
from schemas.deal_schemas import DealCreate, DealUpdate
from schemas.invoice_schemas import InvoiceCreate, InvoiceUpdate
from schemas.lead_schemas import LeadCreate
from schemas.product_schemas import EntityTypeAbbr

from ..base_services.base_service import BaseEntityClient
from ..exceptions import BitrixApiError
from ..products.product_bitrix_services import ProductBitrixClient
from ..timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from .deal_bitrix_services import DealBitrixClient
from .deal_data_provider import DealDataProvider
from .deal_report_helpers import (
    create_dataframe,
    create_excel_file,
    process_deal_row_report,
)
from .deal_repository import DealRepository
from .deal_source_classifier import WEBSITE_CREATOR, identify_source
from .deal_stage_handler import DealStageHandler
from .deal_update_tracker import DealUpdateTracker
from .deal_with_invoice_handler import DealWithInvioceHandler
from .enums import (
    EXCLUDE_FIELDS_FOR_COMPARE,
    CreationSourceEnum,
    DealSourceEnum,
    DealTypeEnum,
)
from .site_order_handler import SiteOrderHandler

SOURCE_SITE_ORDER = "21"
STAGE_INVOICE_FAIL = "DT31_1:D"


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

        self.stage_handler = DealStageHandler(self)
        self.data_provider = DealDataProvider(self)
        self.update_tracker = DealUpdateTracker()
        self.site_order_handler = SiteOrderHandler(self)
        self.deal_with_invoice_handler = DealWithInvioceHandler(self)

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
        logger.info(f"Preparing deal report from {start_date} to {end_date}")

        try:
            deals = await self.repo.fetch_deals(start_date, end_date)
            if not deals:
                logger.warning(f"No deals found for {start_date}-{end_date}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No deals found in specified period",
                )

            return [await process_deal_row_report(deal) for deal in deals]
        except Exception as e:
            logger.error(f"Failed to prepare deal report: {str(e)}")
            raise

    async def export_deals_to_excel(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Основной метод экспорта сделок в Excel"""
        logger.info(
            f"Exporting deals to Excel from {start_date} to {end_date}"
        )

        try:
            data = await self._prepare_data_report(start_date, end_date)
            df = await create_dataframe(data)
            return await create_excel_file(df)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Export failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export error: {str(e)}",
            ) from e

    async def handle_deal(self, external_id: int) -> bool | None:
        """Обрабатывает сделку"""
        try:
            self.update_tracker.reset()
            self.data_provider.clear_cache()
            self.update_tracker.init_deal(external_id)

            deal_b24, deal_db, changes = await self.get_changes_b24_db(
                external_id, exclude_fields=EXCLUDE_FIELDS_FOR_COMPARE
            )
            logger.debug(f"Changes detected for deal {external_id}: {changes}")

            if not deal_b24:
                error_msg = f"Deal with id={external_id} not found"
                logger.error(error_msg)
                raise BitrixApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error=error_msg,
                )

            result = await self._handle_deal(deal_b24, deal_db, changes)
            if not result:
                logger.warning(f"Deal {external_id} processing returned False")
                return None

            if self.update_tracker.has_changes() or changes:
                sync_result = await self._synchronize_deal_data(
                    deal_b24, deal_db, changes
                )
                logger.info(
                    f"Deal {external_id} synchronization "
                    f"{'succeeded' if sync_result else 'failed'}"
                )
                return sync_result
            logger.info(
                f"Deal {external_id} processed successfully with no changes"
            )
            return None
        except Exception as e:
            logger.error(f"Error processing deal {external_id}: {str(e)}")
            raise
        finally:
            self.data_provider.clear_cache()
            self.update_tracker.reset()
            logger.info(f"Finished processing deal {external_id}")

    async def _handle_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> bool | None:
        """Обработка сделки"""
        logger.debug(f"Handling deal {deal_b24.external_id}")

        try:
            invoice = await self.data_provider.get_invoice_data(deal_b24)

            if deal_db and deal_db.is_frozen:
                logger.info(f"Deal {deal_b24.external_id} is frozen")
                return await self._handle_frozen_deal(deal_b24, changes)

            if deal_b24.stage_semantic_id == StageSemanticEnum.FAIL:
                logger.info(f"Deal {deal_b24.external_id} is in FAIL stage")
                return await self._handle_fail_stage_deal(
                    deal_b24, deal_db, invoice, changes
                )

            if invoice is None:
                logger.info(f"Deal {deal_b24.external_id} has no invoice")
                return await self._handle_deal_without_invoice(
                    deal_b24, deal_db, changes
                )
            else:
                logger.info(f"Deal {deal_b24.external_id} has invoice")
                return await self._handle_deal_with_invoice(
                    deal_b24, deal_db, invoice, changes
                )
        except Exception as e:
            logger.error(
                f"Error processing deal {deal_b24:external_id}: {str(e)}"
            )
            raise

    async def _handle_frozen_deal(
        self,
        deal_b24: DealCreate,
        changes: dict[str, dict[str, Any]] | None,
    ) -> bool:
        """Обработка замороженной сделки"""
        # TODO: Реализовать логику обработки замороженной сделки: Откат товаров
        logger.info(f"Processing frozen deal: {deal_b24.external_id}")
        if not changes:
            return True
        deal_update = DealUpdate(external_id=deal_b24.external_id)
        for key, value in changes.items():
            setattr(deal_update, key, value["external"])
        await self.bitrix_client.update(deal_update)
        return True

    async def _handle_fail_stage_deal(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        invoice: InvoiceCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> bool:
        """Обработка провала сделки"""
        logger.info(f"Processing fail deal: {deal_b24.external_id}")

        await self._check_source(deal_b24, deal_db)

        if deal_b24.stage_id != deal_b24.current_stage_id:
            self.update_tracker.update_field(
                "current_stage_id", deal_b24.stage_id, deal_b24
            )
        if invoice:
            if (
                invoice.invoice_stage_id != STAGE_INVOICE_FAIL
                or invoice.current_stage_id != STAGE_INVOICE_FAIL
            ):
                invoice_update_data: dict[str, Any] = {
                    "external_id": invoice.external_id,
                    "stage_id": STAGE_INVOICE_FAIL,
                    "current_stage_id": STAGE_INVOICE_FAIL,
                }
                invoice_update = InvoiceUpdate(**invoice_update_data)
                try:
                    invoice_service = await self.repo.get_invoice_client()
                    await invoice_service.bitrix_client.update(invoice_update)
                    if invoice.external_id and isinstance(
                        invoice.external_id, int
                    ):
                        await invoice_service.import_from_bitrix(
                            int(invoice.external_id)
                        )
                    if invoice.is_loaded:
                        ...  # TODO: send in 1C to delete invoice
                except Exception as e:
                    logger.error(
                        f"Failed to update invoice ID {invoice.external_id}: "
                        f"{str(e)}"
                    )
                    ...
                    # return False

        return True

    async def _handle_deal_without_invoice(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> bool:
        """Обработка сделки без счёта"""
        logger.info(f"Processing deal without invoice: {deal_b24.external_id}")

        await self.site_order_handler.check_new_site_order(deal_b24)

        external_id = self.get_external_id(deal_b24)
        if external_id is None:
            logger.error(
                f"Deal {deal_b24.external_id} has no valid external ID"
            )
            return False

        current_stage = await self._get_current_stage_order(deal_b24)
        if not current_stage:
            logger.error(
                "Cannot determine current stage for deal "
                f"{deal_b24.external_id}"
            )
            return False

        await self._check_source(deal_b24, deal_db)

        product_client = self.product_bitrix_client
        products = await product_client.check_update_products_entity(
            external_id, EntityTypeAbbr.DEAL
        )
        # TODO: Если товары заменялись, тогда сообщение ответственному,
        # кроме заказов с сайта.
        if products:
            self.data_provider.set_cached_products(products)
            logger.debug(
                f"Cached {products.count_products} products for deal "
                f"{external_id}"
            )

        if deal_b24.source_id and deal_b24.source_id == SOURCE_SITE_ORDER:
            await self.site_order_handler.handle_site_order(deal_b24)

        available_stage = await self.stage_handler.check_available_stage(
            deal_b24
        )
        if (
            current_stage
            and available_stage
            and current_stage != available_stage
        ):
            stage_id = await self.repo.get_external_id_by_sort_order_stage(
                available_stage
            )
            self.update_tracker.update_field("stage_id", stage_id, deal_b24)
        return True

    async def _get_current_stage_order(
        self, deal_b24: DealCreate
    ) -> int | None:
        """Получает информацию о текущем этапе сделки"""
        current_stage_name = deal_b24.stage_id
        current_stage = await self.repo.get_sort_order_by_external_id_stage(
            current_stage_name
        )

        if not current_stage:
            logger.warning(
                "Cannot find stage information for deal: "
                f"{deal_b24.external_id}"
            )

        return current_stage

    async def _handle_deal_with_invoice(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        invoice: InvoiceCreate,
        changes: dict[str, dict[str, Any]] | None,
    ) -> bool:
        """Обработка сделки с выставленным счётом"""
        logger.info(f"Processing existing deal: {deal_b24.external_id}")

        return await self.deal_with_invoice_handler.handle_deal_with_invoice(
            deal_b24, deal_db, invoice, changes
        )

    def get_external_id(self, deal_b24: DealCreate) -> int | None:
        if not deal_b24.external_id:
            return None
        try:
            return int(deal_b24.external_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid external_id format: {deal_b24.external_id}")
            return None

    async def _synchronize_deal_data(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
        changes: dict[str, dict[str, Any]] | None,
    ) -> bool:
        """Синхронизирует данные сделки между Bitrix24 и базой данных"""
        logger.info(f"Synchronizing deal data for {deal_b24.external_id}")
        try:
            deal_update = self.update_tracker.get_deal_update()
            # Обновляем данные в Bitrix24
            await self.bitrix_client.update(deal_update)

            # Обновляем или создаем запись в базе данных
            # Добавляем изменённые атрибуты.
            if changes:
                for key, change in changes.items():
                    if getattr(deal_update, key) is None:
                        setattr(deal_update, key, change["internal"])
                        # self.update_tracker.update_field(
                        #    key, change["internal"], deal_b24
                        # )

            if deal_db:
                await self.repo.update_entity(deal_update)
                logger.debug(
                    f"Updated deal {deal_b24.external_id} in database"
                )
            else:
                await self.repo.create_entity(deal_b24)
                logger.debug(
                    f"Created new deal {deal_b24.external_id} in database"
                )

            logger.info(
                f"Successfully synchronized deal {deal_b24.external_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to synchronize deal {deal_b24.external_id}: {str(e)}"
            )
            return False

    async def _check_source(
        self,
        deal_b24: DealCreate,
        deal_db: DealCreate | None,
    ) -> bool:
        """Проверка и определение источника сделки"""
        try:
            needs_update = False
            creation_source_id = deal_b24.creation_source_id
            source_id = deal_b24.source_id
            type_id = deal_b24.type_id
            context: dict[str, Any] = {}
            if deal_db and deal_db.is_setting_source:
                creation_corr = CreationSourceEnum.from_value(
                    deal_db.creation_source_id
                )
                type_corr = DealTypeEnum.from_value(deal_db.type_id)
                source_corr = DealSourceEnum.from_value(deal_db.source_id)
            else:
                result = await identify_source(
                    deal_b24,
                    self.get_lead,
                    self.get_company,
                    self.get_comments,
                    context=context,
                )
                if "company" in context:
                    self.data_provider.set_cached_company(context["company"])
                creation_corr, type_corr, source_corr = result
                logger.info(
                    f"{deal_b24.title} - comparison of source changes:"
                    f"{CreationSourceEnum.get_display_name(creation_corr)}"
                    f":{creation_source_id}, "
                    f"{DealTypeEnum.get_display_name(type_corr)}:{type_id}, "
                    f"{DealSourceEnum.get_display_name(source_corr)}:"
                    f"{source_id}"
                )

            needs_update |= await self._update_field_if_needed(
                deal_b24,
                "creation_source_id",
                creation_source_id,
                creation_corr.value,
            )

            needs_update |= await self._update_field_if_needed(
                deal_b24,
                "source_id",
                source_id,
                source_corr.value,
            )

            needs_update |= await self._update_field_if_needed(
                deal_b24,
                "type_id",
                type_id,
                type_corr.value,
            )
            needs_update |= await self._handle_assignment(
                deal_b24, creation_corr
            )
            logger.debug(
                f"Source check for deal {deal_b24.external_id} completed, "
                f"updates needed: {needs_update}"
            )
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
        field_name: str,
        current_value: Any,
        correct_value: Any,
    ) -> bool:
        """
        Обновляет поле сделки, если текущее значение отличается от корректного
        """
        if current_value != correct_value:
            self.update_tracker.update_field(
                field_name, correct_value, deal_b24
            )
            logger.info(
                f"Updated {field_name} from {current_value} to {correct_value}"
            )
            return True
        return False

    async def _handle_assignment(
        self,
        deal_b24: DealCreate,
        creation_source: CreationSourceEnum,
    ) -> bool:
        """
        Обрабатывает назначение ответственного в зависимости от источника
        сделки
        """
        needs_update = False

        if creation_source == CreationSourceEnum.AUTO:
            if deal_b24.assigned_by_id != WEBSITE_CREATOR:
                self.update_tracker.update_field(
                    "assigned_by_id", WEBSITE_CREATOR, deal_b24
                )
                logger.info(
                    "Assigned to website creator for auto-created deal"
                )
        else:
            if not await self._check_active_manager(deal_b24.assigned_by_id):
                self.update_tracker.update_field(
                    "assigned_by_id", WEBSITE_CREATOR, deal_b24
                )
                logger.info(
                    "Reassigned to website creator due to inactive manager"
                )

        return needs_update

    async def _check_active_manager(self, manager_id: int) -> bool:
        """Проверка активных менеджеров"""
        logger.debug(f"Checking if manager {manager_id} is active")
        try:
            user_service = await self.repo.get_user_client()
            return await user_service.repo.is_activity_manager(manager_id)
        except Exception as e:
            logger.error(f"Failed to check manager {manager_id}: {str(e)}")
            return False

    async def get_lead(self, lead_id: int) -> LeadCreate | None:
        """Получение лида по ID"""
        logger.debug(f"Getting lead with ID: {lead_id}")
        try:
            lead_service = await self.repo.get_lead_client()
            return await lead_service.bitrix_client.get(lead_id)
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {str(e)}")
            return None

    async def get_company(self, company_id: int) -> CompanyCreate | None:
        """Получение компании по ID"""
        logger.debug(f"Getting company with ID: {company_id}")
        try:
            company_service = await self.repo.get_company_client()
            return await company_service.bitrix_client.get(company_id)
        except Exception as e:
            logger.error(f"Failed to get company {company_id}: {str(e)}")
            return None

    async def get_invoice(self, deal_id: int) -> InvoiceCreate | None:
        """Получение счёта по ID сделки"""
        logger.debug(f"Getting invoice for deal ID: {deal_id}")
        try:
            invoice_service = await self.repo.get_invoice_client()
            return await invoice_service.bitrix_client.get_invoice_by_deal_id(
                deal_id
            )
        except Exception as e:
            logger.error(f"Failed to get invoice of deal {deal_id}: {str(e)}")
            return None

    async def get_contact(self, contact_id: int) -> ContactCreate | None:
        """Получение контакта по ID"""
        logger.debug(f"Getting contact with ID: {contact_id}")
        try:
            contact_service = await self.repo.get_contact_client()
            return await contact_service.bitrix_client.get(contact_id)
        except Exception as e:
            logger.error(f"Failed to get contact {contact_id}: {str(e)}")
            return None

    async def get_comments(self, deal_id: int) -> str:
        """Получает комментарии сделки"""
        logger.debug(f"Getting comments for deal ID: {deal_id}")
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

    async def update_comments(
        self, comment: str, deal_b24: DealCreate
    ) -> bool:
        """Обновляет комментарии сделки"""
        logger.debug(f"Updating comments for deal {deal_b24.external_id}")
        try:
            comments_deal = deal_b24.comments
            comments_new = None
            if not comments_deal:
                comments_new = comment
            else:
                if comment in comments_deal:
                    return False
                comments_new = (
                    f"<div>{comments_deal}</div><div>{comment}<br></div>"
                )
                self.update_tracker.update_field(
                    "comments", comments_new, deal_b24
                )
            return True

        except Exception as e:
            logger.error(
                "Failed to update comments for deal "
                f"{deal_b24.external_id}: {str(e)}"
            )
            return False
