import base64
import mimetypes
import re
from typing import Any
from urllib.parse import unquote, urlparse

import requests  # type: ignore[import-untyped]
from fastapi import Request, status
from fastapi.responses import JSONResponse

from core.logger import logger
from core.settings import settings

from ..bitrix_services.base_bitrix_client import BaseBitrixClient
from ..bitrix_services.webhook_service import WebhookService


class ProductHandler(BaseBitrixClient):
    """Обработчик товаров для вебхуков Битрикс24"""

    def __init__(self) -> None:
        super().__init__()
        self.portal: str = settings.BOLASHAQ_BITRIX_PORTAL
        self.webhook_service = WebhookService(
            {"ONCRMPRODUCTUPDATE", "ONCRMPRODUCTADD"},
            {settings.BOLASHAQ_WEB_HOOK_PRODUCT_UPDATE_TOKEN: self.portal},
        )

    async def product_processing(self, request: Request) -> JSONResponse:
        """
        Основной метод обработки вебхука товаров
        """
        try:
            logger.info("Starting product processing webhook")

            webhook_payload = await self.webhook_service.process_webhook(
                request
            )

            if not webhook_payload or not webhook_payload.deal_id:
                logger.warning("Webhook received but no product ID found")
                return self._success_response(
                    "Webhook received but no product ID found"
                )

            product_id = webhook_payload.deal_id
            logger.info(f"Processing product ID: {product_id}")

            success = await self._transformation_fields(product_id)

            if success:
                logger.info(f"Successfully processed product ID: {product_id}")
                return self._success_response(
                    f"Successfully processed product ID: {product_id}"
                )
            else:
                logger.error(f"Failed to process product ID: {product_id}")
                return self._error_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    f"Failed to process product ID: {product_id}",
                    "error",
                )

        except Exception as e:
            logger.error(
                f"Error in product_processing: {str(e)}", exc_info=True
            )
            return self._error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Error in product_processing: {str(e)}",
                "error",
            )

    async def _transformation_fields(self, product_id: int) -> bool:
        """
        Преобразование полей товара

        Args:
            product_id: ID товара в Битрикс24

        Returns:
            bool: Успешность преобразования
        """
        try:
            logger.debug(
                f"Starting field transformation for product {product_id}"
            )

            # Получаем данные товара
            product_data = await self._get_product_data(product_id)
            if not product_data:
                logger.error(f"Product {product_id} not found or empty result")
                return False

            # Формируем поля для обновления
            update_fields = await self._prepare_update_fields(product_data)
            update_image = await self._prepare_update_image(product_data)
            update_fields.update(update_image)
            if not update_fields:
                logger.debug(f"No fields to update for product {product_id}")
                return True
            # Обновляем товар
            success = await self._update_product(product_id, update_fields)

            if success:
                logger.info(f"Successfully updated product {product_id}")
            else:
                logger.error(f"Failed to update product {product_id}")

            return success

        except Exception as e:
            logger.error(
                "Error in _transformation_fields for product "
                f"{product_id}: {str(e)}",
                exc_info=True,
            )
            return False

    async def _get_product_data(
        self, product_id: int
    ) -> dict[str, Any] | None:
        """Получение данных товара по ID"""
        try:
            url = (
                f"https://{self.portal}{settings.BOLASHAQ_WEB_HOOK_TOKEN}"
                "crm.product.get"
            )
            response = await self._get(url=url, params={"id": product_id})
            return response.get("result")

        except Exception as e:
            logger.error(f"Error getting product {product_id} data: {str(e)}")
            return None

    async def _prepare_update_fields(
        self, product_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Подготовка полей для обновления"""
        try:
            fields_mapping = [
                ("PROPERTY_121", "PROPERTY_123", "Технические характеристики"),
                ("PROPERTY_127", "PROPERTY_125", "Комплект поставки"),
            ]

            update_fields: dict[str, Any] = {}

            for source_field, target_field, title in fields_mapping:
                field_update = self._get_single_field_update(
                    product_data, source_field, target_field, title
                )
                if field_update:
                    update_fields.update(field_update)

            return update_fields

        except Exception as e:
            logger.error(f"Error preparing update fields: {str(e)}")
            return {}

    def _get_single_field_update(
        self,
        product_data: dict[str, Any],
        source_field: str,
        target_field: str,
        title: str,
    ) -> dict[str, Any]:
        """
        Получение обновления для одного поля

        Args:
            product_data: Данные товара
            source_field: Исходное поле
            target_field: Целевое поле
            title: Заголовок для HTML

        Returns:
            dict: Поля для обновления или пустой словарь
        """
        try:
            source_value = self._extract_field_value(
                product_data, source_field
            )
            target_value = self._extract_field_value(
                product_data, target_field
            )

            fields: dict[str, Any] = {}

            # Если исходное значение пустое, очищаем целевое поле
            if not source_value:
                if target_value:
                    fields[target_field] = {"value": {"TEXT": "", "TYPE": ""}}
                return fields

            # Парсим и преобразуем значение
            parsed_value = self._parse_to_html(source_value, title)

            # Обновляем только если значения отличаются
            if target_value != parsed_value:
                fields[target_field] = {
                    "value": {"TEXT": parsed_value, "TYPE": "HTML"}
                }

            return fields

        except Exception as e:
            logger.error(
                f"Error processing field {source_field} -> "
                f"{target_field}: {str(e)}"
            )
            return {}

    def _extract_field_value(
        self, product_data: dict[str, Any], field_name: str
    ) -> str | None:
        """Извлечение значения поля из данных товара"""
        try:
            field_data: dict[str, Any] | None = product_data.get(
                field_name, {}
            )
            if isinstance(field_data, dict):
                return field_data.get("value", {}).get("TEXT")  # type: ignore
            return None
        except Exception as e:
            logger.warning(f"Error extracting field {field_name}: {str(e)}")
            return None

    def _parse_to_html(self, text: str, title: str) -> str:
        """
        Парсит текст и преобразует в HTML формат

        Args:
            text: Исходный текст
            title: Заголовок для блока

        Returns:
            str: HTML форматированный текст
        """
        if not text:
            return ""

        try:
            # Разбиваем текст на строки и очищаем от лишних пробелов
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            # Формируем HTML
            html_parts = [
                f"<strong>{title}</strong>",
                '<ul style="list-style: none; padding-left: 1;">',
            ]

            for line in lines:
                # Экранируем специальные HTML символы
                line = line.replace("<br>", "")
                escaped_line = (
                    line.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&#39;")
                )
                html_parts.append(f"<li>{escaped_line}</li>")

            html_parts.append("</ul>")

            return "\n".join(html_parts)

        except Exception as e:
            logger.error(f"Error parsing text to HTML: {str(e)}")
            return f"<strong>{title}</strong><p>{text}</p>"

    async def _prepare_update_image(
        self, product_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Подготовка полей для обновления"""
        try:
            preview_pictures: dict[str, Any] | None = product_data.get(
                "DETAIL_PICTURE", {}
            )
            if isinstance(preview_pictures, dict):
                if int(preview_pictures.get("id", 0)) > 0:
                    return {}
            galery_pictures: list[dict[str, Any]] | None = product_data.get(
                "PROPERTY_101", []
            )
            fields: dict[str, Any] = {}
            if isinstance(galery_pictures, list) and galery_pictures:
                picture_data_id = (
                    galery_pictures[0].get("value", {}).get("id", 0)
                )
                if int(picture_data_id) > 0:
                    link = (
                        f"https://{self.portal}"
                        f"{settings.BOLASHAQ_WEB_HOOK_TOKEN}"
                        "catalog.product.download?fields%5BfieldName%5D="
                        f"property101&fields%5BfileId%5D={picture_data_id}&"
                        f"fields%5BproductId%5D={product_data.get('ID',0)}"
                    )
                    image = self.download_image_from_url(link)
                    if image:
                        fields["DETAIL_PICTURE"] = {
                            "fileData": [
                                image["filename"],
                                image["content"],
                            ]
                        }
                        return fields
            return {}
        except Exception as e:
            logger.warning(f"Error extracting field PREVIEW_PICTURE: {str(e)}")
            return {}

    async def _update_product(
        self, product_id: int, fields: dict[str, Any]
    ) -> bool:
        """Обновление товара в Битрикс24"""
        try:
            url = (
                f"https://{self.portal}{settings.BOLASHAQ_WEB_HOOK_TOKEN}"
                "crm.product.update"
            )
            payload: dict[str, Any] = {"id": product_id, "fields": fields}

            response = await self._post(url=url, payload=payload)

            if response.get("result"):
                logger.debug(f"Successfully updated product {product_id}")
                return True
            else:
                logger.error(
                    "Bitrix API error updating product "
                    f"{product_id}: {response}"
                )
                return False

        except Exception as e:
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return False

    def _success_response(self, message: str, event: str = "") -> JSONResponse:
        """Успешный JSON response"""
        response_data = {"status": "success", "message": message}
        if event:
            response_data["event"] = event

        return JSONResponse(
            status_code=status.HTTP_200_OK, content=response_data
        )

    def _error_response(
        self, status_code: int, message: str, error_type: str
    ) -> JSONResponse:
        """Ответ с ошибкой"""
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "error",
                "message": message,
                "error_type": error_type,
            },
        )

    def download_image_from_url(self, image_url: str) -> dict[str, Any] | None:
        """
        Скачивает изображение по URL и возвращает данные для загрузки

        Returns:
            dict: {'content': base64, 'filename': str, 'content_type': str}
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            print(f"{response.headers}=================")
            # Определяем тип контента и расширение файла
            content_type = response.headers.get("content-type", "image/jpeg")
            extension = mimetypes.guess_extension(content_type) or ".jpg"
            print(f"{content_type}::{extension}")
            filename = (
                self._extract_filename_from_response(response, image_url)
                or f"image{extension}"
            )

            # Если в имени файла нет расширения, добавляем его
            if "." not in filename:
                filename += extension

            # Кодируем в base64
            file_content_base64 = base64.b64encode(response.content).decode(
                "utf-8"
            )

            return {
                "content": file_content_base64,
                "filename": filename,
                "content_type": content_type,
                "file_size": len(response.content),
            }

        except Exception as e:
            print(f"❌ Error downloading image from {image_url}: {e}")
            return None

    def _extract_filename_from_response(
        self, response: requests.Response, fallback_url: str
    ) -> str | None:
        """
        Извлекает имя файла из HTTP response

        Приоритет:
        1. Content-Disposition header (filename*)
        2. Content-Disposition header (filename)
        3. URL path
        """
        headers = response.headers

        # 1. Пробуем извлечь из Content-Disposition (filename*)
        content_disposition = headers.get("Content-Disposition", "")
        if content_disposition:
            # Ищем filename* (с кодировкой)
            match = re.search(
                r"filename\*=([^;]+)", content_disposition, re.IGNORECASE
            )
            if match:
                filename = match.group(1).strip()
                filename = filename.strip("\"'")
                if filename.lower().startswith("utf-8''"):
                    return unquote(filename[7:])
                return unquote(filename)

            # Ищем обычный filename
            match = re.search(
                r"filename=([^;]+)", content_disposition, re.IGNORECASE
            )
            if match:
                filename = match.group(1).strip()
                filename = filename.strip("\"'")
                return unquote(filename)

        # 2. Пробуем извлечь из URL
        parsed_url = urlparse(fallback_url)
        url_filename = parsed_url.path.split("/")[-1]
        if url_filename and "." in url_filename:
            return url_filename

        return None


def get_products_service() -> ProductHandler:
    return ProductHandler()
