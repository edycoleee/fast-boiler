from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from app.modules.auth.dependencies import require_permission
from app.modules.news.schemas import ApiMeta, ApiResponse
from app.modules.media.service import MediaService

router = APIRouter(
    prefix="/api/v1/media",
    tags=["media-api"],
    dependencies=[Depends(require_permission("media.manage"))],
)

media_service = MediaService()


def _meta(request: Request) -> ApiMeta:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return ApiMeta(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/upload", response_model=ApiResponse)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
):
    result = await media_service.upload_file(file)
    return ApiResponse(
        success=True,
        message="File uploaded successfully.",
        data=result.model_dump(),
        meta=_meta(request),
    )


@router.get("/list", response_model=ApiResponse)
def list_media(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
):
    items = media_service.list_recent_files(limit=limit)
    return ApiResponse(
        success=True,
        message="Media list fetched.",
        data=[item.model_dump() for item in items],
        meta=_meta(request),
    )
