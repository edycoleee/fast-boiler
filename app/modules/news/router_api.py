from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import ApiMeta, ApiResponse, NewsCreate, NewsOut, NewsUpdate
from app.modules.news.service import NewsService

router = APIRouter(prefix="/api/v1/news", tags=["news-api"])


def get_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(NewsRepository(db))


def _meta(request: Request, *, page: int | None = None, per_page: int | None = None, total: int | None = None) -> ApiMeta:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return ApiMeta(
        request_id=request_id,
        timestamp=datetime.now(timezone.utc),
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("")
def api_list_news(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    service: NewsService = Depends(get_service),
):
    items, total, page, per_page = service.list_news(page=page, per_page=per_page)
    data = [NewsOut.model_validate(item) for item in items]
    return ApiResponse[list[NewsOut]](
        success=True,
        message="News fetched",
        data=data,
        meta=_meta(request, page=page, per_page=per_page, total=total),
    )


@router.get("/{news_id}")
def api_get_news(news_id: int, request: Request, service: NewsService = Depends(get_service)):
    item = service.get_news_by_id(news_id)
    return ApiResponse[NewsOut](
        success=True,
        message="News fetched",
        data=NewsOut.model_validate(item),
        meta=_meta(request),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def api_create_news(payload: NewsCreate, request: Request, service: NewsService = Depends(get_service)):
    item = service.create_news(payload, actor_user_id=None)
    return ApiResponse[NewsOut](
        success=True,
        message="News created",
        data=NewsOut.model_validate(item),
        meta=_meta(request),
    )


@router.put("/{news_id}")
def api_update_news(news_id: int, payload: NewsUpdate, request: Request, service: NewsService = Depends(get_service)):
    item = service.update_news(news_id, payload, actor_user_id=None)
    return ApiResponse[NewsOut](
        success=True,
        message="News updated",
        data=NewsOut.model_validate(item),
        meta=_meta(request),
    )


@router.delete("/{news_id}")
def api_delete_news(news_id: int, request: Request, service: NewsService = Depends(get_service)):
    service.delete_news(news_id)
    return ApiResponse[dict[str, str]](
        success=True,
        message="News deleted",
        data={"id": str(news_id)},
        meta=_meta(request),
    )
