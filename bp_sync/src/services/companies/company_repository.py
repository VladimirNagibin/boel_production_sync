from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from db.postgres import Base
from models.bases import EntityType
from models.company_models import Company as CompanyDB
from models.contact_models import Contact as ContactDB
from models.deal_documents import Contract
from models.lead_models import Lead as LeadDB
from models.references import (
    ContactType,
    Currency,
    DealFailureReason,
    DealType,
    Emploees,
    Industry,
    MainActivity,
    ShippingCompany,
    Source,
)
from models.user_models import User as UserDB
from schemas.company_schemas import CompanyCreate, CompanyUpdate

from ..base_repositories.base_communication_repo import (
    EntityWithCommunicationsRepository,
)
from ..deals.deal_contract_handler import DealContractHandler
from ..exceptions import CyclicCallException
from ..users.user_services import UserClient

if TYPE_CHECKING:
    from ..contacts.contact_services import ContactClient
    from ..entities.source_services import SourceClient
    from ..leads.lead_services import LeadClient


class CompanyRepository(
    EntityWithCommunicationsRepository[
        CompanyDB, CompanyCreate, CompanyUpdate, int
    ]
):

    model = CompanyDB
    entity_type = EntityType.COMPANY

    def __init__(
        self,
        session: AsyncSession,
        get_contact_client: Callable[[], Coroutine[Any, Any, "ContactClient"]],
        get_lead_client: Callable[[], Coroutine[Any, Any, "LeadClient"]],
        get_user_client: Callable[[], Coroutine[Any, Any, UserClient]],
        get_source_client: Callable[[], Coroutine[Any, Any, "SourceClient"]],
    ):
        super().__init__(session)
        self.get_contact_client = get_contact_client
        self.get_lead_client = get_lead_client
        self.get_user_client = get_user_client
        self.get_source_client = get_source_client

    async def create_entity(self, data: CompanyCreate) -> CompanyDB:
        """Создает новый контакт с проверкой связанных объектов"""
        await self._check_related_objects(data)
        try:
            await self._create_or_update_related(data)
        except CyclicCallException:
            if not data.external_id:
                logger.error("Update failed: Missing ID")
                raise ValueError("ID is required for update")
            external_id = data.external_id
            data = CompanyCreate.get_default_entity(int(external_id))
        return await self.create(
            data=data,
            post_commit_hook=self._handel_contracts_post_commit_hook,
        )

    async def update_entity(
        self, data: CompanyCreate | CompanyUpdate
    ) -> CompanyDB:
        """Обновляет существующий контакт"""
        await self._check_related_objects(data)
        await self._create_or_update_related(data)
        return await self.update(
            data=data,
            post_commit_hook=self._handel_contracts_post_commit_hook,
        )

    async def _get_related_checks(self) -> list[tuple[str, Type[Base], str]]:
        """Возвращает специфичные для Deal проверки"""
        return [
            # (атрибут схемы, модель БД, поле в модели)
            ("currency_id", Currency, "external_id"),
            ("company_type_id", ContactType, "external_id"),
            ("main_activity_id", MainActivity, "ext_alt3_id"),
            ("deal_failure_reason_id", DealFailureReason, "ext_alt3_id"),
            ("deal_type_id", DealType, "external_id"),
            ("shipping_company_id", ShippingCompany, "external_id"),
            ("industry_id", Industry, "external_id"),
            ("employees_id", Emploees, "external_id"),
        ]

    async def _get_related_create(self) -> dict[str, tuple[Any, Any, bool]]:
        """Возвращает кастомные проверки для дочерних классов"""
        lead_client = await self.get_lead_client()
        contact_client = await self.get_contact_client()
        user_client = await self.get_user_client()
        source_client = await self.get_source_client()
        return {
            "lead_id": (lead_client, LeadDB, False),
            "contact_id": (contact_client, ContactDB, False),
            "assigned_by_id": (user_client, UserDB, True),
            "created_by_id": (user_client, UserDB, True),
            "modify_by_id": (user_client, UserDB, False),
            "last_activity_by": (user_client, UserDB, False),
            "source_id": (source_client, Source, False),
        }

    async def get_external_id_by_name(self, name: str) -> int | None:
        """
        Получить external_id компании отгрузки по названию

        Args:
            name: Название компании отгрузки

        Returns:
            external_id компании или None, если не найдена
        """
        try:
            stmt = select(ShippingCompany.external_id).where(
                ShippingCompany.name == name
            )
            result = await self.session.execute(stmt)
            external_id = result.scalar_one_or_none()
            return external_id  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при поиске компании по названию '{name}': {e}"
            )
            raise RuntimeError(
                f"Не удалось найти компанию по названию: {name}"
            ) from e

    async def get_id_by_name(self, name: str) -> UUID | None:
        """
        Получить id компании отгрузки по названию

        Args:
            name: Название компании отгрузки

        Returns:
            id компании или None, если не найдена
        """
        try:
            stmt = select(ShippingCompany.id).where(
                ShippingCompany.name == name
            )
            result = await self.session.execute(stmt)
            id = result.scalar_one_or_none()
            return id  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при поиске компании по названию '{name}': {e}"
            )
            raise RuntimeError(
                f"Не удалось найти компанию по названию: {name}"
            ) from e

    async def get_external_id_by_ext_alt_id(
        self, ext_alt_id: int
    ) -> int | None:
        """
        Получить external_id компании отгрузки по ext_alt_id

        Args:
            ext_alt_id: Альтернативный ID компании отгрузки

        Returns:
            external_id компании или None, если не найдена
        """
        try:
            stmt = select(ShippingCompany.external_id).where(
                ShippingCompany.ext_alt_id == ext_alt_id
            )
            result = await self.session.execute(stmt)
            external_id = result.scalar_one_or_none()
            return external_id  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при поиске компании по ext_alt_id '{ext_alt_id}': {e}"
            )
            raise RuntimeError(
                f"Не удалось найти компанию по ext_alt_id: {ext_alt_id}"
            ) from e

    async def get_ext_alt_id_by_external_id(
        self, external_id: int
    ) -> int | None:
        """
        Получить ext_alt_id компании отгрузки по external_id

        Args:
            external_id: ID компании отгрузки

        Returns:
            ext_alt_id компании или None, если не найдена
        """
        try:
            stmt = select(ShippingCompany.ext_alt_id).where(
                ShippingCompany.external_id == external_id
            )
            result = await self.session.execute(stmt)
            ext_alt_id = result.scalar_one_or_none()
            return ext_alt_id  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(
                "Ошибка при поиске компании по ext_alt_id "
                f"'{external_id}': {e}"
            )
            raise RuntimeError(
                f"Не удалось найти компанию по ext_alt_id: {external_id}"
            ) from e

    async def _handel_contracts_post_commit_hook(
        self, obj: CompanyDB, data: CompanyCreate | CompanyUpdate
    ) -> None:
        """Обрабатывает контракты после создания/обновления компании"""
        if not hasattr(data, "contracts") or not data.contracts:
            await self._mark_all_contracts_as_deleted(obj.id)
            return

        processed_contracts: set[str] = set()

        for contract_str in data.contracts:
            try:
                contract_number = await self._process_single_contract(
                    contract_str, obj.id
                )
                if contract_number:
                    processed_contracts.add(contract_number)
            except Exception as e:
                logger.error(
                    f"Ошибка обработки контракта '{contract_str}': {e}"
                )
                continue
        await self._mark_missing_contracts_as_deleted(
            obj.id, processed_contracts
        )

    async def _process_single_contract(
        self, contract_str: str, company_id: UUID
    ) -> str | None:
        """Обрабатывает один контракт"""
        contract_data = DealContractHandler.parse_contract_info(contract_str)

        if not contract_data.get("firm") or not contract_data["firm"]:
            logger.warning("Пропуск контракта без указания фирмы")
            return None

        shipping_company_id = await self.get_id_by_name(contract_data["firm"])
        if not shipping_company_id:
            logger.error(f"Фирма '{contract_data['firm']}' не найдена")
            return None

        contract_record = await self._prepare_contract_record(
            contract_data, company_id, shipping_company_id
        )
        if not contract_record["number_contract"]:
            logger.warning(
                f"Пропуск контракта с пустым номером: {contract_str}"
            )
            return None
        existing_contract = await self._find_existing_contract(
            company_id, shipping_company_id, contract_record["number_contract"]
        )

        if existing_contract:
            await self._update_existing_contract(
                existing_contract, contract_record
            )
        else:
            await self._create_new_contract(contract_record)

        return contract_record["number_contract"]  # type: ignore

    async def _mark_all_contracts_as_deleted(self, company_id: UUID) -> None:
        """Помечает все контракты компании как удаленные в Битриксе"""
        try:
            stmt = select(Contract).where(
                Contract.company_id == company_id,
                Contract.is_deleted_in_bitrix.is_(False),
            )
            result = await self.session.execute(stmt)
            contracts = result.scalars().all()

            for contract in contracts:
                contract.is_deleted_in_bitrix = True
                logger.info(
                    f"Контракт {contract.number_contract} помечен как "
                    "удаленный в Битриксе"
                )

            if contracts:
                await self.session.flush()
                logger.info(
                    f"Все контракты компании {company_id} помечены как "
                    "удаленные в Битриксе"
                )
            else:
                logger.info(
                    f"У компании {company_id} нет контрактов для пометки как "
                    "удаленных"
                )

        except Exception as e:
            logger.error(
                "Ошибка при пометке всех контрактов как удаленных для "
                f"компании {company_id}: {e}"
            )
            raise

    async def _mark_missing_contracts_as_deleted(
        self, company_id: UUID, processed_contract_numbers: set[str]
    ) -> None:
        """
        Помечает как удаленные контракты, которых нет в обработанном списке
        """
        try:
            # Находим все контракты компании
            stmt = select(Contract).where(
                Contract.company_id == company_id,
                Contract.is_deleted_in_bitrix.is_(False),
            )
            result = await self.session.execute(stmt)
            all_contracts = result.scalars().all()

            contracts_marked = 0
            for contract in all_contracts:
                if contract.number_contract not in processed_contract_numbers:
                    contract.is_deleted_in_bitrix = True
                    contracts_marked += 1
                    logger.info(
                        f"Контракт {contract.number_contract} помечен как "
                        "удаленный в Битриксе"
                    )

            if contracts_marked > 0:
                await self.session.flush()
                logger.info(
                    f"Помечено {contracts_marked} контрактов как удаленные в "
                    f"Битриксе для компании {company_id}"
                )
            else:
                logger.info(
                    "Не найдено контрактов для пометки как удаленных у "
                    f"компании {company_id}"
                )

        except Exception as e:
            logger.error(
                "Ошибка при пометке отсутствующих контрактов как удаленных "
                f"для компании {company_id}: {e}"
            )
            raise

    async def _prepare_contract_record(
        self,
        contract_data: dict[str, str | None],
        company_id: UUID,
        shipping_company_id: UUID,
    ) -> dict[str, Any]:
        """Подготавливает данные контракта для сохранения"""
        contract_number = contract_data.get("contract_number", "б/н")
        if not contract_number or contract_number.strip() == "":
            contract_number = "б/н"
        return {
            "shipping_company_id": shipping_company_id,
            "company_id": company_id,
            "type_contract": (
                contract_data.get("contract_type") or "С покупателем"
            ),
            "number_contract": contract_number,
            "date_contract": (
                self._parse_date(contract_data.get("contract_date"))
            ),
            "period_contract": (
                self._parse_date(contract_data.get("contract_period"))
            ),
        }

    async def _find_existing_contract(
        self, company_id: UUID, shipping_company_id: UUID, contract_number: str
    ) -> Contract | None:
        """Находит существующий контракт"""
        try:
            stmt = select(Contract).where(
                Contract.company_id == company_id,
                Contract.shipping_company_id == shipping_company_id,
                Contract.number_contract == contract_number,
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()  # type: ignore[no-any-return]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка поиска контракта: {e}")
            return None

    async def _update_existing_contract(
        self, contract: Contract, contract_record: dict[str, Any]
    ) -> None:
        """Обновляет существующий контракт"""
        try:
            if (
                contract_record.get("type_contract")
                and contract.type_contract != contract_record["type_contract"]
            ):
                contract.type_contract = contract_record["type_contract"]

            if (
                contract_record.get("date_contract")
                and contract.date_contract != contract_record["date_contract"]
            ):
                contract.date_contract = contract_record["date_contract"]

            if (
                contract_record.get("period_contract")
                and contract.period_contract
                != contract_record["period_contract"]
            ):
                contract.period_contract = contract_record["period_contract"]

            if contract.is_deleted_in_bitrix:
                contract.is_deleted_in_bitrix = False

            await self.session.flush()
            logger.info(f"Контракт {contract.number_contract} обновлен")

        except Exception as e:
            logger.error(
                f"Ошибка обновления контракта {contract.number_contract}: {e}"
            )
            raise

    async def _create_new_contract(
        self, contract_record: dict[str, Any]
    ) -> None:
        """Создает новый контракт"""
        try:
            contract = Contract(**contract_record)
            self.session.add(contract)
            await self.session.flush()
            logger.info(f"Создан новый контракт: {contract.number_contract}")

        except Exception as e:
            logger.error(f"Ошибка создания контракта: {e}")
            raise

    @staticmethod
    def _parse_date(date_str: str | None) -> date | None:
        """Парсит строку даты в объект date"""
        if not date_str:
            return None

        try:
            formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y.%m.%d"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            logger.warning(f"Неизвестный формат даты: {date_str}")
            return None
        except Exception as e:
            logger.error(f"Ошибка парсинга даты '{date_str}': {e}")
            return None
