from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.excel import excel_response
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


@router.get("/export/recent-drafts.xlsx")
def dashboard_export_recent_drafts(
    request: Request,
    draft_service: DraftService = Depends(get_draft_service),
) -> Response:
    user_id = int(request.session.get("user_id"))
    items = draft_service.list_recent(user_id=user_id, limit=500)
    rows = [[item.entity_type, item.entity_key, item.preview_title, item.updated_at.isoformat()] for item in items]
    return excel_response(
        filename_prefix="dashboard-recent-drafts",
        sheet_name="RecentDrafts",
        headers=["Entity Type", "Entity Key", "Draft Title", "Updated At"],
        rows=rows,
    )


@router.get("/export/recent-canvas.xlsx")
def dashboard_export_recent_canvas(
    request: Request,
    canvas_service: CanvasService = Depends(get_canvas_service),
) -> Response:
    user_id = int(request.session.get("user_id"))
    items = canvas_service.list_documents(user_id=user_id, limit=500)
    rows = [[item.document_key, item.title, item.updated_at.isoformat()] for item in items]
    return excel_response(
        filename_prefix="dashboard-recent-canvas",
        sheet_name="RecentCanvas",
        headers=["Document Key", "Title", "Updated At"],
        rows=rows,
    )
