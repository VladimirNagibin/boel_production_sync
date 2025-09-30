from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import APIKeyHeader

from services.dependencies import get_code_service, request_context
from services.products.code_services import CodeService

upload_codes_router = APIRouter(dependencies=[Depends(request_context)])

API_KEY_NAME = "X-API-Key"
API_KEY = "your-api-key-here"  # В продакшене храните в переменных окружения

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


@upload_codes_router.post(  # type: ignore[misc]
    "/upload-codes", summary="Upload product codes file"
)
async def upload_codes_file(
    file: UploadFile = File(..., description="TXT file with product codes"),
    code_service: CodeService = Depends(get_code_service),
    api_key: str = Depends(verify_api_key),
) -> dict[str, Any]:
    # Проверка формата файла
    if file.filename and not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt files are allowed",
        )

    # Сохранение файла
    success = await code_service.save_uploaded_file(file)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the file",
        )

    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "codes_loaded": code_service.get_codes_count(),
    }


@upload_codes_router.get(  # type: ignore[misc]
    "/reload-codes", summary="Reload codes from file"
)
def reload_codes(
    code_service: CodeService = Depends(get_code_service),
    api_key: str = Depends(verify_api_key),
) -> dict[str, Any]:
    code_service.load_codes()
    return {"status": "success", "code_count": code_service.get_codes_count()}
