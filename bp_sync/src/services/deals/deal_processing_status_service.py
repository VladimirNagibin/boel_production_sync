from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Generator

from core.logger import logger
from models.enums import ProcessingStatusEnum
from schemas.deal_schemas import DealUpdate

from ..helpers.date_servise import DateService
from .deal_repository import DealRepository
from .enums import NotificationScopeEnum

if TYPE_CHECKING:
    from models.deal_models import Deal as DealDB

    from .deal_services import DealClient

CHUNK_SIZE = 50
CHAT_SUPERVISOR = 4883


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
            updates: list["DealDB"] = []
            commands: dict[str, Any] = {}
            for deal in deals:
                external_id = deal.external_id
                old_status = deal.processing_status
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
        self, dictionary: dict[str, Any], chunk_size: int = CHUNK_SIZE
    ) -> Generator[dict[str, Any], None, None]:
        """Генератор, который возвращает части словаря по одной"""
        items = list(dictionary.items())
        for i in range(0, len(items), chunk_size):
            yield dict(items[i : i + chunk_size])

    async def send_notifications_overdue_deals(
        self,
        notification_scope: int = NotificationScopeEnum.SUPERVISOR,
        chat_supervisor: int = CHAT_SUPERVISOR,
    ) -> None:
        notifications = await self.get_formatted_data_overdue_deals(
            notification_scope,
            chat_supervisor,
        )
        for notification in notifications:
            await self.deal_client.bitrix_client.send_message_b24(
                *notification
            )

    async def get_formatted_data_overdue_deals(
        self,
        notification_scope: int = NotificationScopeEnum.SUPERVISOR,
        chat_supervisor: int = CHAT_SUPERVISOR,
    ) -> list[tuple[int, str, bool]]:
        """
        Форматирует данные о просроченных сделках в читаемое сообщение и
        определяем список получателей
        """
        notifications: list[tuple[int, str, bool]] = []
        send_supervisor = notification_scope in (
            NotificationScopeEnum.SUPERVISOR,
            NotificationScopeEnum.ALL,
        )
        try:
            deals = await self.deal_client.repo.get_overdue_deals()
            if not deals:
                # logger
                if send_supervisor:
                    return [(chat_supervisor, "Нет просроченных сделок", True)]
                return []
            deals_data = await self.transform_overdue_deals_data(deals)
            if not deals_data:
                # logger
                if send_supervisor:
                    return [
                        (
                            chat_supervisor,
                            "Нет данных для отображения просроченных сделок",
                            True,
                        )
                    ]
                return []
            title = "Список просроченных сделок:"
            message_parts: list[str] = []

            for user_key, user_deals in deals_data.items():
                user_name, chat_id, user_id = user_key
                result = self._format_manager_message(
                    user_name, chat_id, user_id, user_deals
                )
                message, chanel_id, chanel_type = result
                if notification_scope in (
                    NotificationScopeEnum.MANAGERS,
                    NotificationScopeEnum.ALL,
                ):
                    notifications.append(
                        (chanel_id, f"{title}\n{message}", chanel_type)
                    )
                if message:
                    message_parts.append(message)
                    message_parts.append("")
            if send_supervisor:
                if message_parts:
                    message_all = "\n".join(message_parts)
                    notifications.append(
                        (chat_supervisor, f"{title}\n{message_all}", True)
                    )
            return notifications

        except Exception as e:
            logger.error(f"Error formatting overdue deals data: {e}")
            if send_supervisor:
                return [
                    (
                        chat_supervisor,
                        f"Error formatting overdue deals data: {e}",
                        True,
                    )
                ]
            return []

    async def transform_overdue_deals_data(
        self, deals_db: list["DealDB"]
    ) -> dict[tuple[str, int | None, int], list[dict[str, Any]]]:
        """
        Преобразует данные сделок в структурированный формат

        Returns:
            dict: {
                ("Имя Фамилия", chat_id, user_id): [
                    {
                        "stage": "Название стадии",
                        "link": "ссылка",
                        "opportunity": 1000.0,
                        "external_id": 123
                    }
                ]
            }
        """
        deals_by_user: dict[
            tuple[str, int | None, int], list[dict[str, Any]]
        ] = {}

        for deal in deals_db:
            try:
                user_name = deal.assigned_user.full_name
                chat_id = None
                if deal.assigned_user.manager:
                    chat_id = deal.assigned_user.manager.chat_id
                user_id = deal.assigned_user.external_id
                deal_link = self.deal_client.bitrix_client.get_formatted_link(
                    deal.external_id, deal.title
                )

                deal_data: dict[str, Any] = {
                    "stage": deal.stage.name,
                    "link": deal_link,
                    "opportunity": deal.opportunity,
                    "external_id": deal.external_id,
                    "moved_date": deal.moved_date,
                }
                user_key = (user_name, chat_id, user_id)
                if user_key not in deals_by_user:
                    deals_by_user[user_key] = []

                deals_by_user[user_key].append(deal_data)

            except Exception as e:
                logger.error(
                    f"Error transforming deal {deal.external_id}: {e}"
                )
                continue

        return deals_by_user

    def _format_manager_message(
        self,
        user_name: str,
        chat_id: int | None,
        user_id: int,
        deals: list[dict[str, Any]],
    ) -> tuple[str, int, bool]:
        """Форматирует сообщение для конкретного менеджера"""
        message_parts = [f" {user_name}"]

        for deal in deals:
            overdue_days = self.date_service.get_working_days_diff(
                deal["moved_date"], datetime.now(timezone.utc)
            )

            message_parts.append(
                f"   • Стадия: {deal['stage']}, "
                f"Сумма: {deal['opportunity']:,.2f}, "
                f"Просрочено: {overdue_days} дн. "
                f"{deal['link']}"
            )
        if chat_id:
            return "\n".join(message_parts), chat_id, True
        return "\n".join(message_parts), user_id, False
