from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.dependencies import require_admin_session
from app.modules.canvas.repository import CanvasRepository
from app.modules.canvas.service import CanvasService
from app.modules.drafts.repository import DraftRepository
from app.modules.drafts.service import DraftService

router = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_session)],
)


def get_draft_service(db: Session = Depends(get_db)) -> DraftService:
    return DraftService(DraftRepository(db))


def get_canvas_service(db: Session = Depends(get_db)) -> CanvasService:
    return CanvasService(CanvasRepository(db))


@router.get("")
def dashboard_home(
    request: Request,
    draft_service: DraftService = Depends(get_draft_service),
    canvas_service: CanvasService = Depends(get_canvas_service),
):
    user_id = int(request.session.get("user_id"))
    recent_drafts = draft_service.list_recent(user_id=user_id, limit=6)
    recent_canvas_documents = canvas_service.list_documents(user_id=user_id, limit=6)
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard/index.html",
        context={"recent_drafts": recent_drafts, "recent_canvas_documents": recent_canvas_documents},
    )
