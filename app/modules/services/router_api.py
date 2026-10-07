from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.news.schemas import ApiMeta, ApiResponse
from app.modules.services.repository import ServicesRepository
from app.modules.services.schemas import ServiceCreate, ServiceOut, ServiceUpdate
from app.modules.services.service import ServicesService

router = APIRouter(prefix="/api/v1/services", tags=["services-api"])


def get_service(db: Session = Depends(get_db)) -> ServicesService:
    return ServicesService(ServicesRepository(db))


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
def api_list_services(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    service: ServicesService = Depends(get_service),
):
    items, total, page, per_page = service.list_services(page=page, per_page=per_page)
    data = [ServiceOut.model_validate(item) for item in items]
    return ApiResponse[list[ServiceOut]](
        success=True,
        message="Services fetched",
        data=data,
        meta=_meta(request, page=page, per_page=per_page, total=total),
    )


@router.get("/{item_id}")
def api_get_service(item_id: int, request: Request, service: ServicesService = Depends(get_service)):
    item = service.get_service_by_id(item_id)
    return ApiResponse[ServiceOut](
        success=True,
        message="Service fetched",
        data=ServiceOut.model_validate(item),
        meta=_meta(request),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def api_create_service(payload: ServiceCreate, request: Request, service: ServicesService = Depends(get_service)):
    item = service.create_service(payload, actor_user_id=None)
    return ApiResponse[ServiceOut](
        success=True,
        message="Service created",
        data=ServiceOut.model_validate(item),
        meta=_meta(request),
    )


@router.put("/{item_id}")
def api_update_service(item_id: int, payload: ServiceUpdate, request: Request, service: ServicesService = Depends(get_service)):
    item = service.update_service(item_id, payload, actor_user_id=None)
    return ApiResponse[ServiceOut](
        success=True,
        message="Service updated",
        data=ServiceOut.model_validate(item),
        meta=_meta(request),
    )


@router.delete("/{item_id}")
def api_delete_service(item_id: int, request: Request, service: ServicesService = Depends(get_service)):
    service.delete_service(item_id)
    return ApiResponse[dict[str, str]](
        success=True,
        message="Service deleted",
        data={"id": str(item_id)},
        meta=_meta(request),
    )
