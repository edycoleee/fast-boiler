from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.pages.repository import PagesRepository
from app.modules.pages.schemas import PageCreate, PageUpdate
from app.modules.pages.service import PagesService

router = APIRouter(prefix="/admin/pages", tags=["pages-admin"], dependencies=[Depends(require_permission("pages.manage"))])


def get_service(db: Session = Depends(get_db)) -> PagesService:
    return PagesService(PagesRepository(db))


@router.get("")
def admin_pages_index(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    q: str = Query(default=""),
    status_filter: str = Query(default="", alias="status_filter"),
    sort: str = Query(default="created_desc"),
    result: str | None = Query(default=None),
    service: PagesService = Depends(get_service),
):
    items, total, page, per_page = service.list_pages(
        page=page,
        per_page=per_page,
        q=q,
        status_filter=status_filter or None,
        sort=sort,
    )
    return templates.TemplateResponse(
        request=request,
        name="admin/pages/index.html",
        context={
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "result": result,
            "q": q,
            "status_filter": status_filter,
            "sort": sort,
        },
    )


@router.get("/new")
def admin_pages_new(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/pages/_form.html",
        context={"mode": "create", "action": "/admin/pages", "item": None},
    )


@router.post("")
def admin_pages_create(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    summary: str = Form(""),
    content: str = Form(...),
    status_value: str = Form("draft", alias="status"),
    service: PagesService = Depends(get_service),
):
    try:
        payload = PageCreate(title=title, slug=slug, summary=summary or None, content=content, status=status_value)
        actor_user_id = int(request.session.get("user_id"))
        service.create_page(payload, actor_user_id=actor_user_id)
    except (ValidationError, HTTPException) as exc:
        error_message = str(exc.detail) if isinstance(exc, HTTPException) else "Validation failed"
        return templates.TemplateResponse(
            request=request,
            name="admin/pages/_form.html",
            context={
                "mode": "create",
                "action": "/admin/pages",
                "item": {"title": title, "slug": slug, "summary": summary, "content": content, "status": status_value},
                "error": error_message,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return RedirectResponse(url="/admin/pages?result=created", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{page_id}/edit")
def admin_pages_edit(page_id: int, request: Request, service: PagesService = Depends(get_service)):
    item = service.get_page_by_id(page_id)
    return templates.TemplateResponse(
        request=request,
        name="admin/pages/_form.html",
        context={"mode": "edit", "action": f"/admin/pages/{item.id}", "item": item},
    )


@router.post("/{page_id}")
def admin_pages_update(
    request: Request,
    page_id: int,
    title: str = Form(...),
    slug: str = Form(...),
    summary: str = Form(""),
    content: str = Form(...),
    status_value: str = Form("draft", alias="status"),
    service: PagesService = Depends(get_service),
):
    try:
        payload = PageUpdate(title=title, slug=slug, summary=summary or None, content=content, status=status_value)
        actor_user_id = int(request.session.get("user_id"))
        service.update_page(page_id, payload, actor_user_id=actor_user_id)
    except (ValidationError, HTTPException) as exc:
        error_message = str(exc.detail) if isinstance(exc, HTTPException) else "Validation failed"
        return templates.TemplateResponse(
            request=request,
            name="admin/pages/_form.html",
            context={
                "mode": "edit",
                "action": f"/admin/pages/{page_id}",
                "item": {"id": page_id, "title": title, "slug": slug, "summary": summary, "content": content, "status": status_value},
                "error": error_message,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return RedirectResponse(url="/admin/pages?result=updated", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{page_id}/delete")
def admin_pages_delete(page_id: int, service: PagesService = Depends(get_service)):
    service.delete_page(page_id)
    return RedirectResponse(url="/admin/pages?result=deleted", status_code=status.HTTP_303_SEE_OTHER)
