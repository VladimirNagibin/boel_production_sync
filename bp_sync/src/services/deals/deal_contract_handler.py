import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from core.logger import logger
from models.enums import DualTypePaymentEnum
from schemas.company_schemas import CompanyCreate, CompanyUpdate
from schemas.deal_schemas import DealCreate

if TYPE_CHECKING:
    from .deal_services import DealClient

BLACK_SYSTEM = 439
BLACK_SYSTEM_DB = 8923
BLACK_SYSTEM_CONTRACT = "Договор   от "
OFFER_COMPANIES = (445, 447, 773)
OFFER_COMPANY_CONTRACT = "Счет-оферта"


class DealContractHandler:
    """Обработчик договоров для сделок"""

    def __init__(self, deal_client: "DealClient"):
        self.deal_client = deal_client

    async def process_contracts(
        self,
        deal_b24: DealCreate,
    ) -> bool:
        """
        Обрабатывает договоры для сделки и обновляет информацию о компании
        Возвращает True, если был найден подходящий договор
        """
        company_b24 = await self.deal_client.data_provider.get_company_data(
            deal_b24
        )
        shipping_company_id = deal_b24.shipping_company_id

        if not shipping_company_id or not company_b24:
            return False

        try:
            company_service = await self.deal_client.repo.get_company_client()
            shipp = await company_service.repo.get_external_id_by_ext_alt_id(
                shipping_company_id
            )

            if not shipp:
                return False

            # Проверяем стандартные условия
            if (
                shipp == company_b24.shipping_company_id
                and shipp == company_b24.shipping_company_obj
                and company_b24.current_contract
            ):
                return True

            # Проверяем договоры компании
            if company_b24.contracts:
                for contract in company_b24.contracts:
                    contract_details = self.parse_contract_info(contract)
                    contract_firm_name = contract_details["firm"]

                    if not contract_firm_name:
                        continue

                    cur_shipp = (
                        await company_service.repo.get_external_id_by_name(
                            contract_firm_name
                        )
                    )
                    if (
                        cur_shipp == shipp
                        and contract_details["contract_info"]
                    ):
                        await self._update_contract_company(
                            shipp,
                            contract_details["contract_info"],
                            company_b24,
                        )
                        return True

            # Обрабатываем специальные случаи
            return await self._handle_special_cases(
                deal_b24, shipp, shipping_company_id, company_b24
            )

        except Exception as e:
            logger.error(f"Failed to process contracts: {str(e)}")
            return False

    async def _handle_special_cases(
        self,
        deal_b24: DealCreate,
        shipp: int,
        shipping_company_id: int,
        company_b24: CompanyCreate,
    ) -> bool:
        """Обрабатывает специальные случаи договоров"""
        if shipping_company_id == BLACK_SYSTEM:
            await self._update_contract_company(
                BLACK_SYSTEM_DB,
                BLACK_SYSTEM_CONTRACT,
                company_b24,
            )
            return True
        if (
            shipping_company_id in OFFER_COMPANIES
            and isinstance(deal_b24.payment_type, tuple)
            and deal_b24.payment_type == DualTypePaymentEnum.PREPAYMENT.value
        ):
            await self._update_contract_company(
                shipp,
                OFFER_COMPANY_CONTRACT,
                company_b24,
            )
            return True
        return False

    async def _update_contract_company(
        self,
        shipping_company_id: int,
        contract: str,
        company_b24: CompanyCreate,
    ) -> bool:
        update_data: dict[str, Any] = {
            "external_id": company_b24.external_id,
            "shipping_company_id": shipping_company_id,
            "shipping_company_obj": shipping_company_id,
            "current_contract": contract,
        }
        company_update = CompanyUpdate(**update_data)

        company_service = await self.deal_client.repo.get_company_client()
        await company_service.bitrix_client.update(company_update)
        setattr(company_b24, "shipping_company_id", shipping_company_id)
        setattr(company_b24, "shipping_company_obj", shipping_company_id)
        setattr(company_b24, "current_contract", contract)
        return True

    @staticmethod
    def parse_contract_info(contract_string: str) -> dict[str, str | None]:
        """
        Разбирает строку с информацией о договоре на составляющие части.

        Args:
            contract_string: строка с информацией о договоре
            for example: "Фирма: Торговый дом СР , вид договора: С покупателем,
                        //Договор № 18/078 от 23.03.2021//, срок действия"
        Returns:
            Словарь с извлеченными данными:
            - firm: название фирмы
            - contract_type: вид договора
            - contract_info: представление договора - номер и дата
            - contract_number: номер договора
            - contract_date: дата договора в формате DD.MM.YYYY
            - contract_term: срок действия договора
        """
        result: dict[str, str | None] = {
            "firm": None,
            "contract_type": None,
            "contract_info": None,
            "contract_number": None,
            "contract_date": None,
            "contract_term": None,
        }

        try:
            # Извлекаем фирму
            firm_match = re.search(r"Фирма:\s*([^,]+)", contract_string)
            if firm_match:
                result["firm"] = firm_match.group(1).strip()

            # Извлекаем вид договора
            contract_type_match = re.search(
                r"вид договора:\s*([^,]+)", contract_string
            )
            if contract_type_match:
                result["contract_type"] = contract_type_match.group(1).strip()

            # Извлекаем информацию о договоре (номер и дату)
            contract_info_match = re.search(r"//([^/]+)//", contract_string)
            if contract_info_match:
                contract_info = contract_info_match.group(1).strip()
                result["contract_info"] = contract_info
                # Извлекаем номер договора
                number_match = re.search(
                    r"Договор\s*[№N]?\s*([\d/]+)", contract_info
                )
                if number_match:
                    result["contract_number"] = number_match.group(1).strip()

                # Извлекаем дату договора
                date_match = re.search(
                    r"от\s*(\d{2}\.\d{2}\.\d{4})", contract_info
                )
                if date_match:
                    contract_date = date_match.group(1).strip()

                    # Проверяем валидность даты
                    try:
                        datetime.strptime(contract_date, "%d.%m.%Y")
                        result["contract_date"] = contract_date
                    except ValueError:
                        result["contract_date"] = None

            # Извлекаем срок действия
            term_match = re.search(
                r"срок действия\s*([^,]+)?$", contract_string
            )
            if term_match and term_match.group(1):
                result["contract_term"] = term_match.group(1).strip()

        except Exception as e:
            # Логирование ошибки при необходимости
            print(f"Ошибка при разборе строки: {e}")

        return result
