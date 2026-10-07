from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse

from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.media.service import MediaService

router = APIRouter(
    prefix="/admin/media",
    tags=["media-admin"],
    dependencies=[Depends(require_permission("media.manage"))],
)

media_service = MediaService()


@router.get("")
def media_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/media/index.html",
        context={
            "success_name": request.query_params.get("uploaded"),
            "error": None,
        },
    )


@router.post("/upload")
async def media_upload(request: Request, file: UploadFile = File(...)):
    try:
        result = await media_service.upload_file(file)
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="admin/media/index.html",
            context={"success_name": None, "error": str(exc.detail)},
            status_code=exc.status_code,
        )
    return RedirectResponse(
        url=f"/admin/media?uploaded={result.original_name}",
        status_code=status.HTTP_303_SEE_OTHER,
    )

