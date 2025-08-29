from typing import TYPE_CHECKING

from core.logger import logger
from schemas.contact_schemas import ContactCreate
from schemas.deal_schemas import DealCreate

if TYPE_CHECKING:
    from .deal_contract_handler import DealContractHandler
    from .deal_services import DealClient

BLACK_SYSTEM = 439
BLACK_SYSTEM_DB = 8923
BLACK_SYSTEM_CONTRACT = "Договор   от "
OFFER_COMPANIES = (445, 447, 773)
OFFER_COMPANY_CONTRACT = "Счет-оферта"


class DealStageHandler:
    """Обработчик стадий сделки"""

    def __init__(self, deal_client: "DealClient"):
        self.deal_client = deal_client
        self.contract_handler = DealContractHandler(deal_client)

    async def check_available_stage(self, deal_b24: DealCreate) -> int:
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
        company = await self.deal_client.data_provider.get_company_data(
            deal_b24
        )
        if company and (company.has_email or company.has_phone):
            return True

        contact = await self.deal_client.data_provider.get_contact_data(
            deal_b24
        )
        if contact and (contact.has_email or contact.has_phone):
            return True

        return False

    async def _has_required_stage3_data(self, deal_b24: DealCreate) -> bool:
        """
        Проверяет наличие данных для перехода на стадию 3:
        - Товары
        - Основная деятельность клиента
        - Город клиента
        """
        # Проверяем наличие товаров
        products = await self.deal_client.data_provider.get_products_data()
        if not (products and products.count_products > 0):
            return False

        # Получаем данные компании
        company = await self.deal_client.data_provider.get_company_data(
            deal_b24
        )

        # Проверяем основную деятельность
        if (
            (not deal_b24.main_activity_id)
            and company
            and company.main_activity_id
        ):
            self.deal_client.update_tracker.update_field(
                "main_activity_id", company.main_activity_id, deal_b24
            )
        if not (
            deal_b24.main_activity_id or (company and company.main_activity_id)
        ):
            return False

        # Проверяем город
        if not deal_b24.city and company and company.city:
            self.deal_client.update_tracker.update_field(
                "city", company.city, deal_b24
            )
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
        company = await self.deal_client.data_provider.get_company_data(
            deal_b24
        )

        if not company:
            contact = await self.deal_client.data_provider.get_contact_data(
                deal_b24
            )
            if contact and contact.company_id:
                company = await self.deal_client.get_company(
                    contact.company_id
                )
                if company:
                    self.deal_client.update_tracker.update_field(
                        "company_id", contact.company_id, deal_b24
                    )
                    self.deal_client.data_provider.set_cached_company(company)
        if (
            (not company)
            and deal_b24.shipping_company_id
            and deal_b24.shipping_company_id == BLACK_SYSTEM
        ):
            company_id = await self._get_default_company(
                deal_b24.assigned_by_id
            )
            if company_id:
                company = await self.deal_client.get_company(company_id)
            if company:
                self.deal_client.update_tracker.update_field(
                    "company_id", company_id, deal_b24
                )
                self.deal_client.data_provider.set_cached_company(company)
                contact = (
                    await self.deal_client.data_provider.get_contact_data(
                        deal_b24
                    )
                )
                if contact:
                    await self._add_contact_comment(contact, deal_b24)

        # Проверяем наличие компании и фирмы отгрузки
        return bool(company and deal_b24.shipping_company_id)

    async def _get_default_company(self, user_id: int) -> int | None:
        try:
            user_service = await self.deal_client.repo.get_user_client()
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
            await self.deal_client.update_comments(comment, deal_b24)

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

    async def _has_required_stage5_data(self, deal_b24: DealCreate) -> bool:
        """
        Проверяет наличие данных для перехода на стадию 5:
        - наличие договора с компанией по фирме отгрузки
        - обработка разных фирм отгрузки
        """
        return await self.contract_handler.process_contracts(deal_b24)
