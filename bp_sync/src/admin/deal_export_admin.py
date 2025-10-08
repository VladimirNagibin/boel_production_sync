from datetime import datetime
from typing import Any

from fastapi import Request
from fastapi.templating import TemplateResponse
from sqladmin import BaseView, expose


class DealExportAdmin(BaseView):  # type: ignore[misc]
    name = "Экспорт сделок"
    icon = "fa-solid fa-file-export"
    category = "Отчеты"

    @expose("/export-deals", methods=["GET", "POST"])  # type: ignore[misc]
    async def export_deals_page(self, request: Request) -> TemplateResponse:
        """
        Упрощенная страница для экспорта сделок
        """
        error = None
        success = None
        export_url = None

        # Устанавливаем даты по умолчанию
        today = datetime.now().date()
        one_month_ago = (
            today.replace(month=today.month - 1)
            if today.month > 1
            else today.replace(year=today.year - 1, month=12)
        )

        start_date_default = one_month_ago.isoformat()
        end_date_default = today.isoformat()

        if request.method == "POST":
            form_data = await request.form()
            start_date = form_data.get("start_date", "").strip()
            end_date = form_data.get("end_date", "").strip()

            try:
                # Валидация дат
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                if start_dt > end_dt:
                    error = "Дата начала не может быть больше даты окончания"
                else:
                    # Формируем URL для существующего endpoint
                    export_url = (
                        f"/api/v1/reports/export-deals/?"
                        f"start_date={start_date}&end_date={end_date}"
                    )
                    success = (
                        "Экспорт настроен. Нажмите на ссылку ниже для "
                        "скачивания файла."
                    )

            except ValueError as e:
                error = f"Ошибка в формате даты: {str(e)}"
            except Exception as e:
                error = f"Произошла ошибка: {str(e)}"

        context: dict[str, Any] = {
            "request": request,
            "error": error,
            "success": success,
            "export_url": export_url,
            "start_date_default": start_date_default,
            "end_date_default": end_date_default,
        }

        return await self.templates.TemplateResponse(
            request, "deal_export.html", context
        )
