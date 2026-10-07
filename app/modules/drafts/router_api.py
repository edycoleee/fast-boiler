from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.modules.drafts.repository import DraftRepository
from app.modules.drafts.schemas import DraftAutosavePayload
from app.modules.drafts.service import DraftService
from app.modules.news.schemas import ApiMeta, ApiResponse

router = APIRouter(prefix="/api/v1/drafts", tags=["drafts-api"])


def _meta(request: Request) -> ApiMeta:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return ApiMeta(request_id=request_id, timestamp=datetime.now(timezone.utc))


def _require_user_id(request: Request) -> int:
    session_user_id = request.session.get("user_id")
    if session_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return int(session_user_id)


def get_service(db: Session = Depends(get_db)) -> DraftService:
    return DraftService(DraftRepository(db))


@router.post("")
def save_draft(payload: DraftAutosavePayload, request: Request, service: DraftService = Depends(get_service)):
    user_id = _require_user_id(request)
    payload_chars = len(str(payload.payload))
    if payload_chars > settings.draft_max_payload_chars:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Draft payload exceeds max {settings.draft_max_payload_chars} chars",
        )
    save_result = service.save_draft(
        user_id=user_id,
        entity_type=payload.entity_type,
        entity_key=payload.entity_key,
        payload=payload.payload,
    )
    return ApiResponse(
        success=True,
        message="Draft throttled" if save_result.throttled else "Draft saved",
        data=save_result.draft.model_dump(mode="json"),
        meta=_meta(request),
    )


@router.get("")
def get_draft(
    request: Request,
    entity_type: str = Query(..., min_length=1, max_length=50),
    entity_key: str = Query(..., min_length=1, max_length=120),
    service: DraftService = Depends(get_service),
):
    user_id = _require_user_id(request)
    draft = service.get_draft(user_id=user_id, entity_type=entity_type, entity_key=entity_key)
    return ApiResponse(
        success=True,
        message="Draft fetched",
        data=draft.model_dump(mode="json") if draft is not None else None,
        meta=_meta(request),
    )


@router.delete("")
def delete_draft(
    request: Request,
    entity_type: str = Query(..., min_length=1, max_length=50),
    entity_key: str = Query(..., min_length=1, max_length=120),
    service: DraftService = Depends(get_service),
):
    user_id = _require_user_id(request)
    service.discard_draft(user_id=user_id, entity_type=entity_type, entity_key=entity_key)
    return ApiResponse(success=True, message="Draft deleted", data={"ok": True}, meta=_meta(request))


@router.get("/recent")
def list_recent_drafts(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    entity_type: str | None = Query(default=None, min_length=1, max_length=50),
    service: DraftService = Depends(get_service),
):
    user_id = _require_user_id(request)
    drafts = service.list_recent(user_id=user_id, limit=limit, entity_type=entity_type)
    return ApiResponse(
        success=True,
        message="Recent drafts fetched",
        data=[item.model_dump(mode="json") for item in drafts],
        meta=_meta(request),
    )
