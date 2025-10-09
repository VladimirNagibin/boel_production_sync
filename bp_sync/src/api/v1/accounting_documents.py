from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from schemas.billing_schemas import BillingCreate
from schemas.delivery_note_schemas import DeliveryNoteCreate
from services.billings.billing_repository import BillingRepository
from services.delivery_notes.delivery_note_repository import (
    DeliveryNoteRepository,
)
from services.dependencies import (
    get_billing_repository_dep,
    get_delivery_note_repository_dep,
    request_context,
)
from services.exceptions import ConflictException

from .deps import verify_api_key

account_router = APIRouter(
    dependencies=[Depends(request_context), Depends(verify_api_key)]
)


@account_router.post("/billing")  # type: ignore
async def create_billing(
    billing_create: BillingCreate,
    billing_repository: BillingRepository = Depends(
        get_billing_repository_dep
    ),
) -> JSONResponse:

    try:
        billing_db = await billing_repository.create_entity(billing_create)
    except ConflictException:
        billing_db = await billing_repository.update_entity(billing_create)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "billing_id": billing_db.external_id,
        },
    )


@account_router.post("/delivery-note")  # type: ignore
async def create_delivery_note(
    delivery_note_create: DeliveryNoteCreate,
    delivery_note_repository: DeliveryNoteRepository = Depends(
        get_delivery_note_repository_dep
    ),
) -> JSONResponse:
    try:
        delivery_note_db = await delivery_note_repository.create_entity(
            delivery_note_create
        )
    except ConflictException:
        delivery_note_db = await delivery_note_repository.update_entity(
            delivery_note_create
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "delivery_note_id": delivery_note_db.external_id,
        },
    )
