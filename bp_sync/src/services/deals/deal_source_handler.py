from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, status

from core.logger import logger
from core.settings import settings
from schemas.deal_schemas import DealUpdate
from services.deals.enums import (
    CreationSourceEnum,
    DealSourceEnum,
    DealTypeEnum,
)

if TYPE_CHECKING:

    from .deal_services import DealClient

USERS_SET_SOURCE = (169, 5095, 215, 171)


@dataclass
class DealSourceData:
    """Data container for deal source information"""

    user_id: str
    key: str
    deal_id: str
    creation_source: str | None
    source: str | None
    type_deal: str | None


class DealSourceHandler:
    """Обработчик источников сделки"""

    def __init__(self, deal_client: "DealClient"):
        self.deal_client = deal_client

    async def set_deal_source(
        self,
        user_id: str,
        key: str,
        deal_id: str,
        creation_source: str | None,
        source: str | None,
        type_deal: str | None,
    ) -> bool:
        source_data = DealSourceData(
            user_id=user_id,
            key=key,
            deal_id=deal_id,
            creation_source=creation_source,
            source=source,
            type_deal=type_deal,
        )

        user_num = self._extract_user_id(user_id)

        try:
            # Validate input
            self._validate_input(source_data)

            # Authorize request
            self._authorize_request(user_num, source_data.key)

            # Skip if no source data provided
            if not self._has_source_data(source_data):
                logger.info(
                    f"No source data provided for deal {deal_id}, skipping "
                    "update"
                )
                return True
        except Exception:
            await self.deal_client.bitrix_client.send_message_b24(
                user_num, "Источники сделки не обновились."
            )
            raise
        # Update deal source
        return await self._update_deal_source(source_data, user_num)

    def _validate_input(self, data: DealSourceData) -> None:
        """Validate input parameters"""
        if not data.deal_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deal ID is required",
            )

    def _authorize_request(self, user_num: int, key: str) -> int:
        """Authorize the request using user ID and secret key"""
        # Validate secret key
        if key != settings.WEB_HOOK_KEY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret key",
            )

        # Validate user permissions
        if user_num not in USERS_SET_SOURCE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"User {user_num} does not have permission to update deal "
                    "sources"
                ),
            )
        return user_num

    def _extract_user_id(self, user_id: str) -> int:
        """Extract numeric user ID from string format 'user_123'"""
        try:
            if user_id.startswith("user_"):
                return int(user_id[5:])
            else:
                return int(user_id)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid user ID format: {user_id}, error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user ID format: {user_id}",
            )

    def _has_source_data(self, data: DealSourceData) -> bool:
        """Check if any source data is provided"""
        return any([data.creation_source, data.source, data.type_deal])

    async def _update_deal_source(
        self, data: DealSourceData, user_num: int
    ) -> bool:
        """Update deal source in Bitrix and local database"""
        try:
            # Prepare update data
            deal_update = self._prepare_deal_update(data)

            # Update in Bitrix
            await self.deal_client.bitrix_client.update(deal_update)
            logger.info(f"Deal {data.deal_id} source updated in Bitrix")

            # Update in local database
            await self._update_local_deal(data.deal_id, deal_update)

            return True

        except Exception as e:
            logger.error(
                f"Failed to update deal {data.deal_id} source: {str(e)}"
            )
            await self.deal_client.bitrix_client.send_message_b24(
                user_num, "Источники сделки не обновились."
            )
            return False

    def _prepare_deal_update(self, data: DealSourceData) -> DealUpdate:
        """Prepare DealUpdate object from source data"""
        deal_data: dict[str, Any] = {
            "external_id": data.deal_id,
            "is_setting_source": True,
        }

        deal_update = DealUpdate(**deal_data)

        # Map source values to enum values
        if data.creation_source:
            try:
                deal_update.creation_source_id = (
                    CreationSourceEnum.get_value_by_display_name(
                        data.creation_source
                    )
                )
            except ValueError as e:
                raise ValueError(
                    f"Invalid creation_source: {data.creation_source}"
                ) from e
        if data.source:
            try:
                deal_update.source_id = (
                    DealSourceEnum.get_value_by_display_name(data.source)
                )
            except ValueError as e:
                raise ValueError(
                    f"Invalid creation_source: {data.source}"
                ) from e
        if data.type_deal:
            try:
                deal_update.type_id = DealTypeEnum.get_value_by_display_name(
                    data.type_deal
                )
            except ValueError as e:
                raise ValueError(
                    f"Invalid creation_source: {data.type_deal}"
                ) from e

        return deal_update

    async def _update_local_deal(
        self, deal_id: str, deal_update: DealUpdate
    ) -> None:
        """Update deal in local database with error handling"""
        try:
            await self.deal_client.repo.update_entity(deal_update)
            logger.info(f"Deal {deal_id} source updated in local database")

        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                # Deal not found locally, import from Bitrix
                logger.info(
                    f"Deal {deal_id} not found locally, importing from Bitrix"
                )
                await self.deal_client.import_from_bitrix(deal_id)
            else:
                # Re-raise other HTTP exceptions
                raise
        except Exception as e:
            logger.error(f"Failed to update local deal {deal_id}: {str(e)}")
            raise
