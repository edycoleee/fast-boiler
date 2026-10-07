from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.canvas.repository import CanvasRepository
from app.modules.canvas.schemas import CanvasRenamePayload, CanvasSavePayload
from app.modules.canvas.service import CanvasService
from app.modules.news.schemas import ApiMeta, ApiResponse

router = APIRouter(prefix="/api/v1/canvas", tags=["canvas-api"])


def _meta(request: Request) -> ApiMeta:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return ApiMeta(request_id=request_id, timestamp=datetime.now(timezone.utc))


def _require_user_id(request: Request) -> int:
    session_user_id = request.session.get("user_id")
    if session_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return int(session_user_id)


def _require_permission(db: Session, user_id: int, permission_code: str) -> None:
    auth_service = AuthService(AuthRepository(db))
    user = auth_service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    if not auth_service.user_has_permission(user, permission_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


def get_service(db: Session = Depends(get_db)) -> CanvasService:
    return CanvasService(CanvasRepository(db))


@router.put("")
def save_canvas(payload: CanvasSavePayload, request: Request, service: CanvasService = Depends(get_service)):
    user_id = _require_user_id(request)
    _require_permission(service.repository.db, user_id, "canvas.manage")
    payload_chars = len(str(payload.payload))
    if payload_chars > settings.canvas_max_payload_chars:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Canvas payload exceeds max {settings.canvas_max_payload_chars} chars",
        )
    try:
        doc = service.save_document_with_conflict_guard(
            user_id=user_id,
            document_key=payload.document_key,
            title=payload.title,
            payload=payload.payload,
            last_known_updated_at=payload.last_known_updated_at,
            force=payload.force,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApiResponse(
        success=True,
        message="Canvas saved",
        data=doc.model_dump(mode="json"),
        meta=_meta(request),
    )


@router.get("")
def get_canvas(
    request: Request,
    document_key: str = Query(default="default", min_length=1, max_length=80),
    service: CanvasService = Depends(get_service),
):
    user_id = _require_user_id(request)
    _require_permission(service.repository.db, user_id, "canvas.read")
    doc = service.get_document(user_id=user_id, document_key=document_key)
    return ApiResponse(
        success=True,
        message="Canvas fetched",
        data=doc.model_dump(mode="json") if doc is not None else None,
        meta=_meta(request),
    )


@router.get("/documents")
def list_canvas_documents(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    service: CanvasService = Depends(get_service),
):
    user_id = _require_user_id(request)
    _require_permission(service.repository.db, user_id, "canvas.read")
    docs = service.list_documents(user_id=user_id, limit=limit)
    return ApiResponse(
        success=True,
        message="Canvas documents fetched",
        data=[item.model_dump(mode="json") for item in docs],
        meta=_meta(request),
    )


@router.patch("")
def rename_canvas_document(payload: CanvasRenamePayload, request: Request, service: CanvasService = Depends(get_service)):
    user_id = _require_user_id(request)
    _require_permission(service.repository.db, user_id, "canvas.manage")
    try:
        result = service.rename_document(
            user_id=user_id,
            document_key=payload.document_key,
            new_document_key=payload.new_document_key,
            title=payload.title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canvas document not found")
    return ApiResponse(
        success=True,
        message="Canvas document renamed",
        data=result.model_dump(mode="json"),
        meta=_meta(request),
    )


@router.delete("")
def delete_canvas_document(
    request: Request,
    document_key: str = Query(..., min_length=1, max_length=80),
    service: CanvasService = Depends(get_service),
):
    user_id = _require_user_id(request)
    _require_permission(service.repository.db, user_id, "canvas.manage")
    deleted = service.delete_document(user_id=user_id, document_key=document_key)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canvas document not found")
    return ApiResponse(
        success=True,
        message="Canvas document deleted",
        data={"ok": True},
        meta=_meta(request),
    )
