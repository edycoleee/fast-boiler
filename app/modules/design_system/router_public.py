from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.templates import templates

router = APIRouter(tags=["design-system-public"])


@router.get("/design-system")
def design_system_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="design-system/index.html",
        context={},
    )

