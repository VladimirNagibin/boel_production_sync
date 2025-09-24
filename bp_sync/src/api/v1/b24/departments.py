from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from services.dependencies import get_department_client_dep, request_context
from services.entities.department_services import DepartmentClient

departments_router = APIRouter(dependencies=[Depends(request_context)])


@departments_router.get(
    "/update-departments",
    summary="Update departments",
    description="Update departments from Bitrix24",
)  # type: ignore
async def update_departments(
    department_client: DepartmentClient = Depends(get_department_client_dep),
) -> JSONResponse:
    result = await department_client.import_from_bitrix()
    return JSONResponse(
        status_code=200,
        content={"updated": len(result)},
    )
