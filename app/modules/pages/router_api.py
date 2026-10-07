from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.news.schemas import ApiMeta, ApiResponse
from app.modules.pages.repository import PagesRepository
from app.modules.pages.schemas import PageCreate, PageOut, PageUpdate
from app.modules.pages.service import PagesService

router = APIRouter(prefix="/api/v1/pages", tags=["pages-api"])


def get_service(db: Session = Depends(get_db)) -> PagesService:
    return PagesService(PagesRepository(db))


def _meta(request: Request, *, page: int | None = None, per_page: int | None = None, total: int | None = None) -> ApiMeta:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return ApiMeta(request_id=request_id, timestamp=datetime.now(timezone.utc), page=page, per_page=per_page, total=total)


@router.get("")
def api_list_pages(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    published_only: bool = Query(default=False),
    service: PagesService = Depends(get_service),
):
    items, total, page, per_page = service.list_pages(page=page, per_page=per_page, published_only=published_only)
    data = [PageOut.model_validate(item) for item in items]
    return ApiResponse[list[PageOut]](
        success=True,
        message="Pages fetched",
        data=data,
        meta=_meta(request, page=page, per_page=per_page, total=total),
    )


@router.get("/{page_id}")
def api_get_page(page_id: int, request: Request, service: PagesService = Depends(get_service)):
    item = service.get_page_by_id(page_id)
    return ApiResponse[PageOut](success=True, message="Page fetched", data=PageOut.model_validate(item), meta=_meta(request))


@router.post("", status_code=status.HTTP_201_CREATED)
def api_create_page(payload: PageCreate, request: Request, service: PagesService = Depends(get_service)):
    item = service.create_page(payload, actor_user_id=None)
    return ApiResponse[PageOut](success=True, message="Page created", data=PageOut.model_validate(item), meta=_meta(request))


@router.put("/{page_id}")
def api_update_page(page_id: int, payload: PageUpdate, request: Request, service: PagesService = Depends(get_service)):
    item = service.update_page(page_id, payload, actor_user_id=None)
    return ApiResponse[PageOut](success=True, message="Page updated", data=PageOut.model_validate(item), meta=_meta(request))


@router.delete("/{page_id}")
def api_delete_page(page_id: int, request: Request, service: PagesService = Depends(get_service)):
    service.delete_page(page_id)
    return ApiResponse[dict[str, str]](success=True, message="Page deleted", data={"id": str(page_id)}, meta=_meta(request))
