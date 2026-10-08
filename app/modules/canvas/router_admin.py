from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.templates import templates
from app.modules.auth.dependencies import require_permission

router = APIRouter(
    prefix="/admin/canvas",
    tags=["canvas-admin"],
    dependencies=[Depends(require_permission("canvas.manage"))],
)


@router.get("")
def canvas_index(request: Request, doc: str = Query(default="default")):
    initial_document_key = doc.strip() or "default"
    return templates.TemplateResponse(
        request=request,
        name="admin/canvas/index.html",
        context={"initial_document_key": initial_document_key},
    )


@router.get("/mode-2")
def canvas_mode_2_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/canvas/mode2.html",
        context={},
    )
