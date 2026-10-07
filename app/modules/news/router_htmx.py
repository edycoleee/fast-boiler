from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService

router = APIRouter(
    prefix="/admin/news/partials",
    tags=["news-htmx"],
    dependencies=[Depends(require_permission("news.manage"))],
)


def get_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(NewsRepository(db))


@router.get("/table")
def news_table_partial(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    q: str = Query(default=""),
    status_filter: str = Query(default="", alias="status_filter"),
    sort: str = Query(default="created_desc"),
    service: NewsService = Depends(get_service),
):
    items, total, page, per_page = service.list_news(
        page=page,
        per_page=per_page,
        q=q,
        status_filter=status_filter or None,
        sort=sort,
    )
    return templates.TemplateResponse(
        request=request,
        name="admin/news/_table.html",
        context={
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "q": q,
            "status_filter": status_filter,
            "sort": sort,
        },
    )


@router.get("/row/{news_id}")
def news_row_partial(news_id: int, request: Request, service: NewsService = Depends(get_service)):
    item = service.get_news_by_id(news_id)
    return templates.TemplateResponse(request=request, name="admin/news/_row.html", context={"item": item})


@router.get("/form")
def news_form_partial(
    request: Request,
    news_id: int | None = None,
    service: NewsService = Depends(get_service),
):
    item = service.get_news_by_id(news_id) if news_id is not None else None
    action = f"/admin/news/{item.id}" if item is not None else "/admin/news"
    mode = "edit" if item is not None else "create"
    return templates.TemplateResponse(
        request=request,
        name="admin/news/_form.html",
        context={"mode": mode, "action": action, "item": item},
    )


@router.get("/filters")
def news_filters_partial(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    q: str = Query(default=""),
    status_filter: str = Query(default="", alias="status_filter"),
    sort: str = Query(default="created_desc"),
):
    return templates.TemplateResponse(
        request=request,
        name="admin/news/_filters.html",
        context={"page": page, "per_page": per_page, "q": q, "status_filter": status_filter, "sort": sort},
    )
