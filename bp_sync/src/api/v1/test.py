from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from services.deals.deal_repository import DealRepository
from services.deals.deal_services import (
    DealClient,
)
from services.dependencies import (
    get_deal_client_dep,
    get_deal_repository_dep,
    get_invoice_client_dep,
    request_context,
)
from services.invoices.invoice_services import InvoiceClient

test_router = APIRouter(dependencies=[Depends(request_context)])


@test_router.get(
    "/test-deal",
    summary="deal handling test",
    description="Test deal handling.",
)  # type: ignore
async def test_deal(
    deal_repo: DealRepository = Depends(get_deal_repository_dep),
    invoice_client: InvoiceClient = Depends(get_invoice_client_dep),
    deal_client: DealClient = Depends(get_deal_client_dep),
) -> JSONResponse:

    deal_id = 56661

    result = await deal_client.handle_deal(deal_id)

    deal_b24, deal_db, changes = await deal_client.get_changes_b24_db(deal_id)

    print(changes)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": result,
        },
    )
