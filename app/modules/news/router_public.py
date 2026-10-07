from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService

router = APIRouter(tags=["news-public"])


def get_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(NewsRepository(db))


@router.get("/news")
def news_index(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    service: NewsService = Depends(get_service),
):
    items, total, page, per_page = service.list_news(page=page, per_page=per_page)
    return templates.TemplateResponse(
        request=request,
        name="public/news/index.html",
        context={"items": items, "page": page, "per_page": per_page, "total": total},
    )


@router.get("/news/{slug}")
def news_detail(
    slug: str,
    request: Request,
    service: NewsService = Depends(get_service),
):
    item = service.get_news_by_slug(slug)
    return templates.TemplateResponse(request=request, name="public/news/detail.html", context={"item": item})
