import os
from datetime import datetime
from enum import Enum
from tempfile import NamedTemporaryFile
from typing import Any, Generator

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pytz import UTC  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Импорт ваших моделей и сессии
from core.logger import logger
from db.postgres import get_session
from models.deal_models import Deal
from models.delivery_note_models import DeliveryNote
from models.invoice_models import Invoice
from models.lead_models import Lead

reports_router = APIRouter()


async def fetch_deals(
    session: AsyncSession, start_date: datetime, end_date: datetime
) -> Any:
    """Асинхронно получает сделки с связанными данными"""
    # Рассчитываем конец периода как начало следующего дня
    result = await session.execute(
        select(Deal)
        .where(Deal.date_create >= start_date, Deal.date_create <= end_date)
        .options(
            # Загрузка отношений для Deal
            selectinload(Deal.assigned_user),
            selectinload(Deal.created_user),
            # selectinload(Deal.modify_user),
            # selectinload(Deal.moved_user),
            selectinload(Deal.type),
            selectinload(Deal.stage),
            selectinload(Deal.source),
            selectinload(Deal.creation_source),
            # Загрузка отношений для Lead
            selectinload(Deal.lead).selectinload(Lead.assigned_user),
            selectinload(Deal.lead).selectinload(Lead.created_user),
            # selectinload(Deal.lead).selectinload(Lead.modify_user),
            # selectinload(Deal.lead).selectinload(Lead.moved_user),
            selectinload(Deal.lead).selectinload(Lead.type),
            selectinload(Deal.lead).selectinload(Lead.status),
            selectinload(Deal.lead).selectinload(Lead.source),
            # Загрузка отношений для Invoice
            selectinload(Deal.invoices).selectinload(Invoice.assigned_user),
            selectinload(Deal.invoices).selectinload(Invoice.created_user),
            # selectinload(Deal.invoices).selectinload(Invoice.modify_user),
            # selectinload(Deal.invoices).selectinload(Invoice.moved_user),
            # selectinload(Deal.invoices).selectinload(Invoice.type),
            selectinload(Deal.invoices).selectinload(Invoice.invoice_stage),
            # selectinload(Deal.invoices).selectinload(Invoice.source),
            # Загрузка отношений для DeliveryNote
            selectinload(Deal.invoices)
            .selectinload(Invoice.delivery_notes)
            .selectinload(DeliveryNote.assigned_user),
            selectinload(Deal.invoices).selectinload(Invoice.billings),
            selectinload(Deal.lead),
            selectinload(Deal.invoices).selectinload(Invoice.delivery_notes),
            selectinload(Deal.invoices).selectinload(Invoice.billings),
        )
    )
    return result.scalars().all()


def get_name(value: Any) -> str:
    """Безопасное получение имени из объекта"""
    if value is None:
        return ""

    # Для пользователей
    if hasattr(value, "full_name") and value.full_name:
        return str(value.full_name)
    if hasattr(value, "name") and value.name:
        return str(value.name)
    if hasattr(value, "title") and value.title:
        return str(value.title)

    # Для перечислений
    if isinstance(value, Enum):
        return value.name

    return ""


def build_data_row(deal: Deal) -> Generator[dict[str, Any], Any, None]:
    """Строит строку данных для экспорта"""
    row: dict[str, Any] = {
        "deal_external_id": deal.external_id,
        "deal_date_create": deal.date_create,
        "deal_assigned_by_id": get_name(deal.assigned_user),
        "deal_created_by_id": get_name(deal.created_user),
        "deal_calltouch_site_id": deal.calltouch_site_id,
        "deal_calltouch_call_id": deal.calltouch_call_id,
        "deal_calltouch_request_id": deal.calltouch_request_id,
        "deal_yaclientid": deal.yaclientid,
        "deal_origin_id": deal.origin_id,
        "deal_title": deal.title,
        "deal_opportunity": deal.opportunity,
        "deal_type_id": get_name(deal.type),
        "deal_stage_id": get_name(deal.stage),
        "deal_source_id": get_name(deal.source),
        "deal_creation_source_id": get_name(deal.creation_source),
    }

    # Данные лида
    if deal.lead:
        row.update(
            {
                "lead_external_id": deal.lead.external_id,
                "lead_date_create": deal.lead.date_create,
                "lead_assigned_by_id": get_name(deal.lead.assigned_user),
                "lead_created_by_id": get_name(deal.lead.created_user),
                "lead_calltouch_site_id": deal.lead.calltouch_site_id,
                "lead_calltouch_call_id": deal.lead.calltouch_call_id,
                "lead_calltouch_request_id": deal.lead.calltouch_request_id,
                "lead_yaclientid": deal.lead.yaclientid,
                "lead_title": deal.lead.title,
                "lead_type_id": get_name(deal.lead.type),
                "lead_status_id": get_name(deal.lead.status),
                "lead_source_id": get_name(deal.lead.source),
            }
        )

    # Данные счетов
    for invoice in deal.invoices:
        invoice_row = row.copy()
        invoice_row.update(
            {
                "invoice_external_id": invoice.external_id,
                "invoice_date_create": invoice.date_create,
                "invoice_assigned_by_id": get_name(invoice.assigned_user),
                "invoice_created_by_id": get_name(invoice.created_user),
                "invoice_calltouch_site_id": invoice.calltouch_site_id,
                "invoice_calltouch_call_id": invoice.calltouch_call_id,
                "invoice_calltouch_request_id": invoice.calltouch_request_id,
                "invoice_yaclientid": invoice.yaclientid,
                "invoice_title": invoice.title,
                "invoice_account_number": invoice.account_number,
                "invoice_is_loaded": invoice.is_loaded,
                "invoice_opportunity": invoice.opportunity,
                "invoice_invoice_stage_id": get_name(invoice.invoice_stage),
                "invoice_total_paid": sum(b.amount for b in invoice.billings),
                "invoice_paid_status": (
                    "paid"
                    if abs(
                        sum(b.amount for b in invoice.billings)
                        - invoice.opportunity
                    )
                    < 0.01
                    else "partial" if any(invoice.billings) else "unpaid"
                ),
            }
        )

        # Данные накладных
        for note in invoice.delivery_notes:
            note_row = invoice_row.copy()
            note_row.update(
                {
                    "delivery_note_external_id": note.external_id,
                    "delivery_note_name": note.name,
                    "delivery_note_opportunity": note.opportunity,
                    "delivery_note_assigned_by_id": (
                        get_name(note.assigned_user)
                    ),
                    "delivery_note_date_delivery_note": (
                        note.date_delivery_note
                    ),
                }
            )
            yield note_row
        else:
            yield invoice_row
    else:
        yield row


def convert_to_naive_datetime(value: Any) -> Any:
    """
    Преобразует datetime с временной зоной в наивный datetime
    (без временной зоны)
    """
    if isinstance(value, datetime) and value.tzinfo is not None:
        # Конвертируем в UTC и удаляем информацию о временной зоне
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


@reports_router.get("/export-deals/")  # type: ignore[misc]
async def export_deals(
    start_date: datetime = Query(
        ..., description="Дата начала в формате YYYY-MM-DD"
    ),
    end_date: datetime = Query(
        ..., description="Дата окончания в формате YYYY-MM-DD"
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    tmp_path = None
    try:
        logger.info(f"Starting export for {start_date} to {end_date}")
        # Асинхронное получение данных
        deals = await fetch_deals(session, start_date, end_date)

        if not deals:
            logger.warning(
                f"No deals found between {start_date} and {end_date}"
            )
            raise HTTPException(
                status_code=404,
                detail="No deals found in the specified date range",
            )

        # Построение данных в синхронном режиме
        logger.info(f"Found {len(deals)} deals, processing...")
        data = []
        for deal in deals:
            for row in build_data_row(deal):
                processed_row = {
                    key: convert_to_naive_datetime(value)
                    for key, value in row.items()
                }
                data.append(processed_row)

        # Создание DataFrame
        df = pd.DataFrame(data)
        logger.info(f"Created DataFrame with {len(df)} rows")

        # Создание временного файла
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            df.to_excel(tmp.name, index=False, engine="openpyxl")
            tmp_path = tmp.name
            logger.info(f"Created temporary Excel file: {tmp_path}")

        # Проверяем размер файла
        file_size = os.path.getsize(tmp_path)
        if file_size == 0:
            logger.error(f"Empty Excel file created at {tmp_path}")
            raise HTTPException(
                status_code=500, detail="Failed to generate Excel file"
            )

        logger.info(f"File size: {file_size} bytes")

        background_tasks.add_task(delete_file, tmp_path)

        return FileResponse(
            tmp_path,
            filename=(
                f"deals_export_{start_date.date()}_to_{end_date.date()}.xlsx"
            ),
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml."
                "sheet"
            ),
            background=background_tasks,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error during export: {str(e)}", exc_info=True)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))


def delete_file(path: str) -> Any:
    """Удаляет файл после отправки"""
    try:
        if os.path.exists(path):
            os.unlink(path)
            logger.info(f"Deleted temporary file: {path}")
    except Exception as e:
        logger.error(f"Error deleting temporary file {path}: {str(e)}")
