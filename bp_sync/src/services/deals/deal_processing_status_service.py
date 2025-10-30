from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generator

from core.logger import logger
from models.deal_models import Deal
from models.enums import ProcessingStatusEnum
from schemas.deal_schemas import DealUpdate

from ..helpers.date_servise import DateService
from .deal_repository import DealRepository

if TYPE_CHECKING:

    from .deal_services import DealClient


class DealProcessingStatusService:
    """Сервис для обновления статусов обработки сделок"""

    def __init__(self, deal_client: "DealClient"):
        self.deal_client = deal_client
        self.date_service = DateService()

    async def update_processing_statuses(
        self, relative_time: datetime | None = None
    ) -> dict[str, int]:
        """
        Основной метод для обновления статусов processing_status
        Возвращает статистику обновлений
        """
        try:
            stats = {"updated": 0, "at_risk": 0, "overdue": 0}
            if relative_time:
                # Если передана относительная дата, используем её
                current_time = relative_time
            else:
                # Иначе используем текущее время
                current_time = datetime.now(timezone.utc)

            repo: DealRepository = self.deal_client.repo
            deals = await repo.get_deals_for_checking_processing_status(
                current_time
            )

            logger.info(f"Found {len(deals)} deals to check for status update")
            if not deals:
                return stats
            updates: list[Deal] = []
            commands: dict[str, Any] = {}
            for deal in deals:
                external_id = deal.external_id
                old_status = deal.processing_status
                # crutch
                deal_b24 = await self.deal_client.bitrix_client.get(
                    external_id
                )
                old_status = deal_b24.processing_status
                # end
                new_status = await self._calculate_new_status(
                    deal.moved_date, current_time
                )

                if old_status != new_status:

                    deal.processing_status = new_status
                    updates.append(deal)
                    commands[f"update_deal_{external_id}"] = (
                        f"crm.deal.update?id={external_id}"
                        f"&fields[UF_CRM_1750571370]={new_status}"
                    )
                    # deal_data: dict[str, Any] = {
                    #    "processing_status": new_status,
                    #    "external_id": deal.external_id,
                    # }
                    # TODO: сделать пакетную загрузку
                    # deal_update = DealUpdate(**deal_data)
                    # await self.deal_client.bitrix_client.update(deal_update)
                    # Обновляем статистику
                    stats["updated"] += 1
                    if new_status == ProcessingStatusEnum.AT_RISK:
                        stats["at_risk"] += 1
                    elif new_status == ProcessingStatusEnum.OVERDUE:
                        stats["overdue"] += 1

                    logger.info(
                        f"Deal {deal.external_id}: {old_status} -> "
                        f"{new_status}, moved_date: {deal.moved_date}"
                    )

            # Сохраняем изменения
            if updates:
                """
                repo.session.add_all(updates)
                await repo.session.commit()
                for commands_chunk in self._dict_chunks(commands):
                    bitrix_client = self.deal_client.bitrix_client
                    result = await bitrix_client.execute_batch(commands_chunk)
                    logger.info(f"Successfully updated in B24: {result}")
                logger.info(
                    f"Successfully updated {stats['updated']} deals: "
                    f"{stats['at_risk']} AT_RISK, {stats['overdue']} OVERDUE"
                )
                """
                ...
            else:
                logger.info("No deals required status updates")

            return stats

        except Exception as e:
            await self.deal_client.repo.session.rollback()
            logger.error(f"Error updating processing statuses: {e}")
            raise

    async def _calculate_new_status(
        self, moved_date: datetime, current_time: datetime
    ) -> ProcessingStatusEnum:
        """Вычисляет новый статус на основе moved_date"""
        working_days_diff = self.date_service.get_working_days_diff(
            moved_date, current_time
        )

        if working_days_diff > 3:
            return ProcessingStatusEnum.OVERDUE
        elif working_days_diff > 2:
            return ProcessingStatusEnum.AT_RISK
        else:
            return ProcessingStatusEnum.NOT_DEFINE

    async def update_single_deal_status(
        self, deal_id: int, relative_time: datetime | None = None
    ) -> bool:
        """Обновляет статус обработки для одной сделки"""
        try:
            deal = await self.deal_client.repo.get(deal_id)
            if not deal:
                logger.warning(f"Deal {deal_id} not found")
                return False

            if (
                deal.is_frozen
                or not deal.moved_date
                or deal.is_deleted_in_bitrix
            ):
                logger.debug(f"Deal {deal_id} is frozen or has no moved_date")
                return False

            # Проверяем, находится ли сделка на первых четырех стадиях
            first_stages = await self.deal_client.repo.get_first_four_stages()
            if deal.stage_id not in first_stages:
                logger.debug(f"Deal {deal_id} not in first four stages")
                return False

            if relative_time:
                # Если передана относительная дата, используем её
                current_time = relative_time
            else:
                # Иначе используем текущее время
                current_time = datetime.now(timezone.utc)
            old_status = deal.processing_status
            new_status = await self._calculate_new_status(
                deal.moved_date, current_time
            )
            if old_status != new_status:
                deal.processing_status = new_status
                await self.deal_client.repo.session.commit()
                deal_data: dict[str, Any] = {
                    "processing_status": new_status,
                    "external_id": deal.external_id,
                }
                deal_update = DealUpdate(**deal_data)
                await self.deal_client.bitrix_client.update(deal_update)
                logger.info(
                    f"Updated deal {deal_id} status: {old_status} -> "
                    f"{new_status}"
                )
                return True
            else:
                logger.debug(f"Deal {deal_id} status unchanged: {old_status}")
                return False

        except Exception as e:
            await self.deal_client.repo.session.rollback()
            logger.error(f"Error updating single deal {deal_id} status: {e}")
            return False

    def _dict_chunks(
        self, dictionary: dict[str, Any], chunk_size: int = 50
    ) -> Generator[dict[str, Any], None, None]:
        """Генератор, который возвращает части словаря по одной"""
        items = list(dictionary.items())
        for i in range(0, len(items), chunk_size):
            yield dict(items[i : i + chunk_size])
