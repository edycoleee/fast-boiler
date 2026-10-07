from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.pages.repository import PagesRepository
from app.modules.pages.service import PagesService

router = APIRouter(prefix="/pages", tags=["pages-public"])


def get_service(db: Session = Depends(get_db)) -> PagesService:
    return PagesService(PagesRepository(db))


@router.get("")
def pages_index(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    service: PagesService = Depends(get_service),
):
    items, total, page, per_page = service.list_pages(page=page, per_page=per_page, published_only=True)
    return templates.TemplateResponse(
        request=request,
        name="public/pages/index.html",
        context={"items": items, "total": total, "page": page, "per_page": per_page},
    )


@router.get("/{slug}")
def pages_detail(slug: str, request: Request, service: PagesService = Depends(get_service)):
    item = service.get_page_by_slug(slug, published_only=True)
    return templates.TemplateResponse(
        request=request,
        name="public/pages/detail.html",
        context={"item": item},
    )
