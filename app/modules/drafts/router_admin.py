from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.dependencies import require_admin_session
from app.modules.drafts.repository import DraftRepository
from app.modules.drafts.service import DraftService

router = APIRouter(
    prefix="/admin/drafts",
    tags=["drafts-admin"],
    dependencies=[Depends(require_admin_session)],
)


def get_service(db: Session = Depends(get_db)) -> DraftService:
    return DraftService(DraftRepository(db))


@router.get("")
def drafts_index(
    request: Request,
    entity_type: str = Query(default="all"),
    sort: str = Query(default="newest", pattern="^(newest|oldest)$"),
    result: str | None = Query(default=None),
    service: DraftService = Depends(get_service),
):
    user_id = int(request.session.get("user_id"))
    normalized_entity_type = None if entity_type == "all" else entity_type
    items = service.list_for_user(user_id=user_id, limit=200, entity_type=normalized_entity_type, sort=sort)
    return templates.TemplateResponse(
        request=request,
        name="admin/drafts/index.html",
        context={"items": items, "entity_type": entity_type, "sort": sort, "result": result},
    )


@router.post("/delete")
def drafts_delete(
    request: Request,
    entity_type: str = Form(...),
    entity_key: str = Form(...),
    service: DraftService = Depends(get_service),
):
    user_id = int(request.session.get("user_id"))
    service.discard_draft(user_id=user_id, entity_type=entity_type, entity_key=entity_key)
    return RedirectResponse(url="/admin/drafts?result=deleted", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/bulk-delete")
def drafts_bulk_delete(
    request: Request,
    draft_refs: list[str] = Form(default=[]),
    service: DraftService = Depends(get_service),
):
    user_id = int(request.session.get("user_id"))
    pairs: list[tuple[str, str]] = []
    for ref in draft_refs:
        if "::" not in ref:
            continue
        entity_type, entity_key = ref.split("::", 1)
        if not entity_type or not entity_key:
            continue
        pairs.append((entity_type, entity_key))
    deleted = service.discard_many(user_id=user_id, pairs=pairs) if pairs else 0
    result = "bulk-deleted" if deleted > 0 else "bulk-empty"
    return RedirectResponse(url=f"/admin/drafts?result={result}", status_code=status.HTTP_303_SEE_OTHER)
