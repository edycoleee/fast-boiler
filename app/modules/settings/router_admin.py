from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.settings.repository import SettingsRepository
from app.modules.settings.schemas import SiteSettingsUpdate
from app.modules.settings.service import SettingsService

router = APIRouter(
    prefix="/admin/settings",
    tags=["settings-admin"],
    dependencies=[Depends(require_permission("settings.manage"))],
)


def get_service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(SettingsRepository(db))


@router.get("")
def admin_settings_index(request: Request, service: SettingsService = Depends(get_service), result: str | None = None):
    values = service.get_site_settings()
    return templates.TemplateResponse(
        request=request,
        name="admin/settings/index.html",
        context={"values": values, "result": result},
    )


@router.post("")
def admin_settings_update(
    request: Request,
    site_name: str = Form(...),
    site_tagline: str = Form(...),
    contact_email: str = Form(...),
    service: SettingsService = Depends(get_service),
):
    try:
        payload = SiteSettingsUpdate(site_name=site_name, site_tagline=site_tagline, contact_email=contact_email)
    except ValidationError:
        values = {"site_name": site_name, "site_tagline": site_tagline, "contact_email": contact_email}
        return templates.TemplateResponse(
            request=request,
            name="admin/settings/index.html",
            context={"values": values, "error": "Validation failed"},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    actor_user_id = int(request.session.get("user_id"))
    service.update_site_settings(payload, actor_user_id=actor_user_id)
    return RedirectResponse(url="/admin/settings?result=updated", status_code=status.HTTP_303_SEE_OTHER)
