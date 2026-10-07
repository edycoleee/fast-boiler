from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.excel import excel_response
from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.media.service import MediaService
from app.modules.services.repository import ServicesRepository
from app.modules.services.schemas import ServiceCreate, ServiceUpdate
from app.modules.services.service import ServicesService

router = APIRouter(
    prefix="/admin/services",
    tags=["services-admin"],
    dependencies=[Depends(require_permission("services.manage"))],
)
media_service = MediaService()


def get_service(db: Session = Depends(get_db)) -> ServicesService:
    return ServicesService(ServicesRepository(db))


@router.get("")
def admin_services_index(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    q: str = Query(default=""),
    status_filter: str = Query(default="", alias="status_filter"),
    sort: str = Query(default="created_desc"),
    result: str | None = Query(default=None),
    service: ServicesService = Depends(get_service),
):
    items, total, page, per_page = service.list_services(
        page=page,
        per_page=per_page,
        q=q,
        status_filter=status_filter or None,
        sort=sort,
    )
    context = {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "result": result,
        "q": q,
        "status_filter": status_filter,
        "sort": sort,
    }
    return templates.TemplateResponse(request=request, name="admin/services/index.html", context=context)


@router.get("/export.xlsx")
def admin_services_export(
    q: str = Query(default=""),
    status_filter: str = Query(default="", alias="status_filter"),
    sort: str = Query(default="created_desc"),
    service: ServicesService = Depends(get_service),
):
    items = service.list_services_for_export(
        q=q,
        status_filter=status_filter or None,
        sort=sort,
    )
    rows = [
        [item.id, item.name, item.slug, item.status, item.created_at.isoformat(), item.updated_at.isoformat()]
        for item in items
    ]
    return excel_response(
        filename_prefix="services-export",
        sheet_name="Services",
        headers=["ID", "Name", "Slug", "Status", "Created At", "Updated At"],
        rows=rows,
    )


@router.get("/new")
def admin_services_new(request: Request):
    recent_media = media_service.list_recent_files(limit=20)
    return templates.TemplateResponse(
        request=request,
        name="admin/services/_form.html",
        context={"mode": "create", "action": "/admin/services", "item": None, "recent_media": recent_media},
    )


@router.post("")
def admin_services_create(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    summary: str = Form(""),
    description: str = Form(...),
    status_value: str = Form("draft", alias="status"),
    service: ServicesService = Depends(get_service),
):
    try:
        payload = ServiceCreate(name=name, slug=slug, summary=summary or None, description=description, status=status_value)
        actor_user_id = int(request.session.get("user_id"))
        service.create_service(payload, actor_user_id=actor_user_id)
    except (ValidationError, HTTPException) as exc:
        error_message = str(exc.detail) if isinstance(exc, HTTPException) else "Validation failed"
        context = {
            "mode": "create",
            "action": "/admin/services",
            "item": {"name": name, "slug": slug, "summary": summary, "description": description, "status": status_value},
            "error": error_message,
            "recent_media": media_service.list_recent_files(limit=20),
        }
        return templates.TemplateResponse(
            request=request,
            name="admin/services/_form.html",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return RedirectResponse(url="/admin/services?result=created", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{item_id}/edit")
def admin_services_edit(item_id: int, request: Request, service: ServicesService = Depends(get_service)):
    item = service.get_service_by_id(item_id)
    recent_media = media_service.list_recent_files(limit=20)
    return templates.TemplateResponse(
        request=request,
        name="admin/services/_form.html",
        context={"mode": "edit", "action": f"/admin/services/{item.id}", "item": item, "recent_media": recent_media},
    )


@router.post("/{item_id}")
def admin_services_update(
    request: Request,
    item_id: int,
    name: str = Form(...),
    slug: str = Form(...),
    summary: str = Form(""),
    description: str = Form(...),
    status_value: str = Form("draft", alias="status"),
    service: ServicesService = Depends(get_service),
):
    try:
        payload = ServiceUpdate(name=name, slug=slug, summary=summary or None, description=description, status=status_value)
        actor_user_id = int(request.session.get("user_id"))
        service.update_service(item_id, payload, actor_user_id=actor_user_id)
    except (ValidationError, HTTPException) as exc:
        error_message = str(exc.detail) if isinstance(exc, HTTPException) else "Validation failed"
        context = {
            "mode": "edit",
            "action": f"/admin/services/{item_id}",
            "item": {"id": item_id, "name": name, "slug": slug, "summary": summary, "description": description, "status": status_value},
            "error": error_message,
            "recent_media": media_service.list_recent_files(limit=20),
        }
        return templates.TemplateResponse(
            request=request,
            name="admin/services/_form.html",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return RedirectResponse(url="/admin/services?result=updated", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{item_id}/delete")
def admin_services_delete(item_id: int, service: ServicesService = Depends(get_service)):
    service.delete_service(item_id)
    return RedirectResponse(url="/admin/services?result=deleted", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{item_id}/duplicate")
def admin_services_duplicate(request: Request, item_id: int, service: ServicesService = Depends(get_service)):
    actor_user_id = int(request.session.get("user_id"))
    service.duplicate_service(item_id, actor_user_id=actor_user_id)
    return RedirectResponse(url="/admin/services?result=duplicated", status_code=status.HTTP_303_SEE_OTHER)
