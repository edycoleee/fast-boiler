from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.services.repository import ServicesRepository
from app.modules.services.service import ServicesService

router = APIRouter(
    prefix="/admin/services/partials",
    tags=["services-htmx"],
    dependencies=[Depends(require_permission("services.manage"))],
)


def get_service(db: Session = Depends(get_db)) -> ServicesService:
    return ServicesService(ServicesRepository(db))


@router.get("/table")
def services_table_partial(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    service: ServicesService = Depends(get_service),
):
    items, total, page, per_page = service.list_services(page=page, per_page=per_page)
    return templates.TemplateResponse(
        request=request,
        name="admin/services/_table.html",
        context={"items": items, "total": total, "page": page, "per_page": per_page},
    )


@router.get("/row/{item_id}")
def services_row_partial(item_id: int, request: Request, service: ServicesService = Depends(get_service)):
    item = service.get_service_by_id(item_id)
    return templates.TemplateResponse(request=request, name="admin/services/_row.html", context={"item": item})


@router.get("/form")
def services_form_partial(
    request: Request,
    item_id: int | None = None,
    service: ServicesService = Depends(get_service),
):
    item = service.get_service_by_id(item_id) if item_id is not None else None
    action = f"/admin/services/{item.id}" if item is not None else "/admin/services"
    mode = "edit" if item is not None else "create"
    return templates.TemplateResponse(
        request=request,
        name="admin/services/_form.html",
        context={"mode": mode, "action": action, "item": item},
    )


@router.get("/filters")
def services_filters_partial(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
):
    return templates.TemplateResponse(
        request=request,
        name="admin/services/_filters.html",
        context={"page": page, "per_page": per_page},
    )
