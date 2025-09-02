from typing import TYPE_CHECKING

from core.logger import logger
from schemas.deal_schemas import DealCreate

if TYPE_CHECKING:
    from .deal_services import DealClient

STAGE_SITE_ORDER_NEW = "WON"
SERVICE_USER_ID = 215
TYPE_SITE_ORDER_NEW = "SALE"
STAGE_NEW = "NEW"


class SiteOrderHandler:
    """Обработчик заказов с сайта"""

    PARSING_FIELDS = {
        "delivery": "DELIVERYSERVICE",
        "name": "CONTACT_FULL_NAME",
        "address": "АДРЕС ДОСТАВКИ",
        "payment": "PAYMENTSYSTEM",
        "comment": "CUSTOMERCOMMENT",
        "orderstatus": "ORDERSTATUS",
    }

    def __init__(self, deal_client: "DealClient"):
        self.deal_client = deal_client

    async def check_new_site_order(
        self,
        deal_b24: DealCreate,
    ) -> bool:
        """Проверка нового заказа с сайта"""
        logger.info(f"Processing new site order: {deal_b24.external_id}")
        try:
            if (
                deal_b24.stage_id == STAGE_SITE_ORDER_NEW
                and deal_b24.assigned_by_id == SERVICE_USER_ID
                and deal_b24.type_id == TYPE_SITE_ORDER_NEW
            ):
                self.deal_client.update_tracker.update_field(
                    "stage_id", STAGE_NEW, deal_b24
                )
            return True
        except Exception as e:
            logger.error(
                f"Error checking site order {deal_b24.external_id}: {str(e)}"
            )
            return False

    async def handle_site_order(
        self,
        deal_b24: DealCreate,
    ) -> bool:
        """Обработка заказа с сайта"""
        logger.info(f"Processing site order: {deal_b24.external_id}")

        try:
            if not deal_b24.additional_info:
                logger.debug(
                    "No additional info for site order: "
                    f"{deal_b24.external_id}"
                )
                return True

            external_id = self.deal_client.get_external_id(deal_b24)
            if external_id is None:
                logger.error(
                    f"Cannot get external ID for deal: {deal_b24.external_id}"
                )
                return False

            add_info_old = await self._get_old_additional_info(external_id)

            parsed_new_info = self._parse_expression(deal_b24.additional_info)
            comments_new = await self._prepare_comments(
                deal_b24.comments,
                parsed_new_info,
                add_info_old,
                deal_b24.additional_info,
            )
            await self._save_and_update_comments(
                external_id, deal_b24.additional_info, comments_new, deal_b24
            )
            return True
        except Exception as e:
            logger.error(
                f"Error handling site order {deal_b24.external_id}: {str(e)}"
            )
            return False

    async def _get_old_additional_info(self, external_id: int) -> str | None:
        """Получает старую дополнительную информацию из базы данных"""
        try:
            add_schema = await self.deal_client.repo.get_add_info_by_deal_id(
                external_id
            )
            return add_schema.comment if add_schema else None
        except Exception as e:
            logger.error(
                "Error getting old additional info for deal "
                f"{external_id}: {str(e)}"
            )
            return None

    async def _prepare_comments(
        self,
        current_comments: str | None,
        parsed_new_info: str,
        old_add_info: str | None,
        new_add_info: str,
    ) -> str:
        """
        Подготавливает новые комментарии на основе старой и новой информации
        """
        try:
            # Если текущих комментариев нет, просто возвращаем новые
            if not current_comments:
                return parsed_new_info

            # Если нет старой информации, проверяем и добавляем новые
            # комментарии
            if not old_add_info:
                if parsed_new_info in current_comments:
                    return current_comments
                else:
                    return (
                        f"{parsed_new_info}<div>{current_comments}<br></div>"
                    )

            # Если информация изменилась, обрабатываем изменения
            if old_add_info != new_add_info:
                parsed_old_info = self._parse_expression(old_add_info)

                # Если старые комментарии найдены, заменяем их
                if parsed_old_info and parsed_old_info in current_comments:
                    return current_comments.replace(
                        parsed_old_info, parsed_new_info
                    )
                else:
                    # Иначе добавляем новые комментарии
                    if not parsed_new_info:
                        return current_comments
                    elif parsed_new_info in current_comments:
                        return current_comments
                    else:
                        return (
                            f"{parsed_new_info}<div>{current_comments}"
                            "<br></div>"
                        )

            # Если информация не изменилась, возвращаем текущие комментарии
            return current_comments

        except Exception as e:
            logger.error(f"Error preparing comments: {str(e)}")
            return current_comments if current_comments else ""

    async def _save_and_update_comments(
        self,
        external_id: int,
        add_info: str,
        comments_new: str,
        deal_b24: DealCreate,
    ) -> None:
        """
        Сохраняет дополнительную информацию и обновляет комментарии при
        необходимости
        """
        try:
            # Сохраняем новую дополнительную информацию
            await self.deal_client.repo.set_add_info_by_deal_id(
                external_id, add_info
            )
            logger.debug(f"Saved additional info for deal {external_id}")

            # Обновляем комментарии, если они изменились
            if comments_new and (
                not deal_b24.comments or (comments_new != deal_b24.comments)
            ):
                self.deal_client.update_tracker.update_field(
                    "comments", comments_new, deal_b24
                )
                logger.info(f"Updated comments for deal {external_id}")

        except Exception as e:
            logger.error(
                "Error saving info or updating comments for deal "
                f"{external_id}: {str(e)}"
            )
            raise

    def _parse_expression(self, expression: str) -> str:
        """Парсит выражение и возвращает отформатированный HTML-комментарий"""
        logger.debug(f"Parsing expression: {expression[:100]}...")

        try:
            # Инициализация данных для парсинга
            parsed_data = {field: "" for field in self.PARSING_FIELDS.keys()}
            active_field = None

            # Разделение и обработка выражения
            parts = expression.split(";")

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # Проверяем, является ли часть ключевым полем
                field_found = False
                for field_name, field_key in self.PARSING_FIELDS.items():
                    if field_key in part:
                        active_field = field_name
                        field_found = True
                        break

                # Если это значение поля, извлекаем его
                if not field_found and active_field:
                    try:
                        # Пытаемся извлечь значение в кавычках
                        if '"' in part:
                            parsed_data[active_field] = part.split('"')[1]
                        else:
                            parsed_data[active_field] = part
                        active_field = None
                    except (IndexError, ValueError) as e:
                        logger.warning(
                            f"Error parsing part '{part}': {str(e)}"
                        )
                        continue

            # Формирование HTML-комментария
            result = self._format_comment_html(parsed_data)
            return result if result else expression

        except Exception as e:
            logger.error(f"Error parsing expression: {str(e)}")
            return expression

    def _format_comment_html(self, parsed_data: dict[str, str]) -> str:
        """Форматирует распарсенные данные в HTML"""
        comment_parts: list[str] = []

        for field in self.PARSING_FIELDS.keys():
            if parsed_data[field]:
                comment_parts.append(f"<div>{parsed_data[field]}</div>")

        if not comment_parts:
            return ""

        # Объединяем части, добавляя <br> между ними
        html_content = comment_parts[0]
        for part in comment_parts[1:]:
            if not html_content.endswith("<br></div>"):
                html_content = html_content.replace("</div>", "<br></div>")
            html_content += part

        return html_content

    def parse_expression_(self, expression: str) -> str:
        """Парсит выражение и возвращает отформатированный HTML-комментарий"""
        # Инициализация переменных
        data = {
            "dostavka": "",
            "oplata": "",
            "comment": "",
            "statuszakaz": "",
            "name": "",
            "adress": "",
        }

        flags = {
            "dostavka": False,
            "oplata": False,
            "comment": False,
            "statuszakaz": False,
            "name": False,
            "adress": False,
        }

        # Разделение и обработка выражения
        arr_infa = expression.split(";")

        for value in arr_infa:
            if "DELIVERYSERVICE" in value:
                flags["dostavka"] = True
            elif flags["dostavka"]:
                data["dostavka"] = value.split('"')[1]
                flags["dostavka"] = False

            elif "CONTACT_FULL_NAME" in value:
                flags["name"] = True
            elif flags["name"]:
                data["name"] = value.split('"')[1]
                flags["name"] = False

            elif "АДРЕС ДОСТАВКИ" in value:
                flags["adress"] = True
            elif flags["adress"]:
                data["adress"] = value.split('"')[1]
                flags["adress"] = False

            elif "PAYMENTSYSTEM" in value:
                flags["oplata"] = True
            elif flags["oplata"]:
                data["oplata"] = value.split('"')[1]
                flags["oplata"] = False

            elif "CUSTOMERCOMMENT" in value:
                flags["comment"] = True
            elif flags["comment"]:
                data["comment"] = value.split('"')[1]
                flags["comment"] = False

            elif "ORDERSTATUS" in value:
                flags["statuszakaz"] = True
            elif flags["statuszakaz"]:
                data["statuszakaz"] = value.split('"')[1]
                flags["statuszakaz"] = False

        # Формирование HTML-комментария
        comments1 = ""
        fields_order = [
            "name",
            "statuszakaz",
            "oplata",
            "adress",
            "dostavka",
            "comment",
        ]

        for field in fields_order:
            if data[field]:
                if comments1:
                    # Если это не первое поле, добавляем <br> к предыдущему div
                    if not comments1.endswith("<br></div>"):
                        comments1 = comments1.replace("</div>", "<br></div>")
                    comments1 += f"<div>{data[field]}</div>"
                else:
                    comments1 = f"<div>{data[field]}</div>"

        return comments1 if comments1 else expression
