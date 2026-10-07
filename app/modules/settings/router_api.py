from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.settings.repository import SettingsRepository
from app.modules.settings.schemas import SiteSettingsUpdate
from app.modules.settings.service import SettingsService

router = APIRouter(prefix="/api/v1/settings", tags=["settings-api"])


def get_service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(SettingsRepository(db))


@router.get("/site")
def api_get_site_settings(service: SettingsService = Depends(get_service)):
    return service.get_site_settings()


@router.put("/site")
def api_update_site_settings(
    payload: SiteSettingsUpdate,
    service: SettingsService = Depends(get_service),
    current_user: User = Depends(require_permission("settings.manage")),
):
    service.update_site_settings(payload, actor_user_id=current_user.id)
    return {"ok": True}
