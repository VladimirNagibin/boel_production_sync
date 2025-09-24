from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from services.companies.company_bitrix_services import CompanyBitrixClient
from services.contacts.contact_bitrix_services import ContactBitrixClient

# from services.deals.deal_bitrix_services import (
#    DealBitrixClient,
# )
from services.deals.deal_repository import DealRepository
from services.deals.deal_services import (
    DealClient,
)
from services.dependencies import (
    get_company_bitrix_client_dep,
    get_contact_bitrix_client_dep,
    get_deal_client_dep,
    get_deal_repository_dep,
    get_invoice_client_dep,
    get_measure_repository_dep,
    get_product_bitrix_client_dep,
    get_timeline_comment_bitrix_client_dep,
    get_timeline_comment_repository_dep,
    request_context,
)
from services.entities.measure_repository import MeasureRepository
from services.exceptions import BitrixAuthError
from services.invoices.invoice_services import InvoiceClient
from services.products.product_bitrix_services import ProductBitrixClient
from services.timeline_comments.timeline_comment_bitrix_services import (
    TimeLineCommentBitrixClient,
)
from services.timeline_comments.timeline_comment_repository import (
    TimelineCommentRepository,
)

# from schemas.product_schemas import EntityTypeAbbr


# from schemas.product_schemas import EntityTypeAbbr


# from services.bitrix_api_client import BitrixAPIClient
# from schemas.contact_schemas import ContactUpdate
# from services.bitrix_services.bitrix_api_client import BitrixAPIClient


test_router = APIRouter(dependencies=[Depends(request_context)])


@test_router.get(
    "/",
    summary="check redis",
    description="Information about persistency redis.",
)  # type: ignore
async def check(
    measure_repo: MeasureRepository = Depends(get_measure_repository_dep),
    product_bitrix_client: ProductBitrixClient = Depends(
        get_product_bitrix_client_dep
    ),
    company_bitrix_client: CompanyBitrixClient = Depends(
        get_company_bitrix_client_dep
    ),
    contact_bitrix_client: ContactBitrixClient = Depends(
        get_contact_bitrix_client_dep
    ),
    # deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    deal_repo: DealRepository = Depends(get_deal_repository_dep),
    invoice_client: InvoiceClient = Depends(get_invoice_client_dep),
    deal_client: DealClient = Depends(get_deal_client_dep),
    # lead_client: DealClient = Depends(get_lead_client),
    # lead_bitrix_client: LeadBitrixClient = Depends(get_lead_bitrix_client),
    # contact_bitrix_client: ContactBitrixClient = Depends(
    #    get_contact_bitrix_client
    # ),
    # token_storage: TokenStorage = Depends(get_token_storage),
    timeline_client: TimeLineCommentBitrixClient = Depends(
        get_timeline_comment_bitrix_client_dep
    ),
    timeline_repo: TimelineCommentRepository = Depends(
        get_timeline_comment_repository_dep
    ),
) -> JSONResponse:

    # deal_id = 54195  # 49935
    # comm = await get_comm(deal_id, timeline_client, timeline_repo)
    # await deal_client.handle_deal(deal_id)
    result = ""  # invoice_client.send_invoice_request_to_fail(123)
    try:
        result = await company_bitrix_client.get(6533)
    except BitrixAuthError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": e.detail,
            },
        )
    # result = await contact_bitrix_client.get(18281)
    if result:
        ...
        # print(f"{result}-------DEAL--UPDATE")
    # print(f"{products_deal}-------DEAL")
    # products_invoice = await product_bitrix_client.get_entity_products(
    #    26309, EntityTypeAbbr.INVOICE)
    # print(f"{products_invoice}-------INVOICE")
    # print(products_deal.equals_ignore_owner(products_invoice))
    # product = await product_bitrix_client.get_product(1245)
    # print(product)
    # lead = LeadCreate.get_defoult_entity(12345)
    # print(lead)
    # res = await deal_client.import_from_bitrix(50301)
    # res = await department_client.import_from_bitrix()
    # res = await deal_bitrix_client.get(51463)
    # res2 = ContactUpdate(**res.model_dump(by_alias=True, exclude_unset=True))
    # print(du.to_bitrix_dict())
    # res3 = await contact_bitrix_client.update(res2)  # 60131)
    # res = await deal_client.refresh_from_bitrix(51975)  # 60131)
    # lead = await lead_bitrix_client.get(59773)
    # res2 = DealUpdate(**res.model_dump(by_alias=True, exclude_unset=True))
    # lead2 = LeadUpdate(**lead.model_dump(by_alias=True, exclude_unset=True))

    # lead2.title = "NEW TEST 2"
    # lead2.phone[0].value_type = "MOBILE"
    # lead2.phone[1].value = "777777777777"
    # res2.shipping_type = 517
    # res2 = LeadUpdate(title="QWERTY")
    # res3 = await lead_bitrix_client.update(lead2)
    # print(res2.title)
    # res3 = await deal_bitrix_client.list(
    #    filter_entity={"ID": 51463},
    #    select=["ID", "TITLE", "OPPORTUNITY"],
    #    start=0,
    # )
    # print(res.result)
    # await token_storage.delete_token("access_token")
    # if res3:
    #     deal_create = DealCreate(**res)
    #     print(res.model_dump())
    #    return JSONResponse(
    #        status_code=status.HTTP_200_OK,
    #        content={
    #            "status": "success",
    #            "bool": [str(type(res)) for res in res3],
    #            # "result": res.to_bitrix_dict(),
    #        },
    #    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "status": "fault",
        },
    )
