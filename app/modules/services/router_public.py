from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.services.repository import ServicesRepository
from app.modules.services.service import ServicesService

router = APIRouter(tags=["services-public"])


def get_service(db: Session = Depends(get_db)) -> ServicesService:
    return ServicesService(ServicesRepository(db))


@router.get("/services")
def services_index(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    service: ServicesService = Depends(get_service),
):
    items, total, page, per_page = service.list_services(page=page, per_page=per_page)
    return templates.TemplateResponse(
        request=request,
        name="public/services/index.html",
        context={"items": items, "total": total, "page": page, "per_page": per_page},
    )


@router.get("/services/{slug}")
def services_detail(slug: str, request: Request, service: ServicesService = Depends(get_service)):
    item = service.get_service_by_slug(slug)
    return templates.TemplateResponse(request=request, name="public/services/detail.html", context={"item": item})
