from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import NewsCreate, NewsUpdate
from app.modules.news.service import NewsService

router = APIRouter(prefix="/admin/news", tags=["news-admin"], dependencies=[Depends(require_permission("news.manage"))])


def get_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(NewsRepository(db))


@router.get("")
def admin_news_index(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    result: str | None = Query(default=None),
    service: NewsService = Depends(get_service),
):
    items, total, page, per_page = service.list_news(page=page, per_page=per_page)
    context = {"items": items, "total": total, "page": page, "per_page": per_page, "result": result}
    return templates.TemplateResponse(request=request, name="admin/news/index.html", context=context)


@router.get("/new")
def admin_news_new(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/news/_form.html",
        context={"mode": "create", "action": "/admin/news", "item": None},
    )


@router.post("")
def admin_news_create(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    excerpt: str = Form(""),
    content: str = Form(...),
    status_value: str = Form("draft", alias="status"),
    service: NewsService = Depends(get_service),
):
    try:
        payload = NewsCreate(title=title, slug=slug, excerpt=excerpt or None, content=content, status=status_value)
        actor_user_id = int(request.session.get("user_id"))
        service.create_news(payload, actor_user_id=actor_user_id)
    except (ValidationError, HTTPException) as exc:
        error_message = str(exc.detail) if isinstance(exc, HTTPException) else "Validation failed"
        context = {
            "mode": "create",
            "action": "/admin/news",
            "item": {"title": title, "slug": slug, "excerpt": excerpt, "content": content, "status": status_value},
            "error": error_message,
        }
        return templates.TemplateResponse(
            request=request,
            name="admin/news/_form.html",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return RedirectResponse(url="/admin/news?result=created", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{news_id}/edit")
def admin_news_edit(news_id: int, request: Request, service: NewsService = Depends(get_service)):
    item = service.get_news_by_id(news_id)
    return templates.TemplateResponse(
        request=request,
        name="admin/news/_form.html",
        context={"mode": "edit", "action": f"/admin/news/{item.id}", "item": item},
    )


@router.post("/{news_id}")
def admin_news_update(
    request: Request,
    news_id: int,
    title: str = Form(...),
    slug: str = Form(...),
    excerpt: str = Form(""),
    content: str = Form(...),
    status_value: str = Form("draft", alias="status"),
    service: NewsService = Depends(get_service),
):
    try:
        payload = NewsUpdate(title=title, slug=slug, excerpt=excerpt or None, content=content, status=status_value)
        actor_user_id = int(request.session.get("user_id"))
        service.update_news(news_id, payload, actor_user_id=actor_user_id)
    except (ValidationError, HTTPException) as exc:
        error_message = str(exc.detail) if isinstance(exc, HTTPException) else "Validation failed"
        context = {
            "mode": "edit",
            "action": f"/admin/news/{news_id}",
            "item": {"id": news_id, "title": title, "slug": slug, "excerpt": excerpt, "content": content, "status": status_value},
            "error": error_message,
        }
        return templates.TemplateResponse(
            request=request,
            name="admin/news/_form.html",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return RedirectResponse(url="/admin/news?result=updated", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{news_id}/delete")
def admin_news_delete(news_id: int, service: NewsService = Depends(get_service)):
    service.delete_news(news_id)
    return RedirectResponse(url="/admin/news?result=deleted", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{news_id}/duplicate")
def admin_news_duplicate(request: Request, news_id: int, service: NewsService = Depends(get_service)):
    actor_user_id = int(request.session.get("user_id"))
    service.duplicate_news(news_id, actor_user_id=actor_user_id)
    return RedirectResponse(url="/admin/news?result=duplicated", status_code=status.HTTP_303_SEE_OTHER)
