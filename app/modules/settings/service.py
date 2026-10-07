from __future__ import annotations

from app.modules.settings.repository import SettingsRepository
from app.modules.settings.schemas import SiteSettingsUpdate


class SettingsService:
    def __init__(self, repository: SettingsRepository) -> None:
        self.repository = repository

    def list_settings(self):
        return self.repository.list_all()

    def get_site_settings(self) -> dict[str, str]:
        default_map = {
            "site_name": "Fast Boiler",
            "site_tagline": "Modern Corporate Landing Template",
            "contact_email": "hello@example.com",
        }
        result = default_map.copy()
        for setting in self.repository.list_all():
            if setting.key in result:
                result[setting.key] = setting.value
        return result

    def update_site_settings(self, payload: SiteSettingsUpdate, *, actor_user_id: int | None = None) -> None:
        self.repository.upsert(key="site_name", value=payload.site_name, actor_user_id=actor_user_id)
        self.repository.upsert(key="site_tagline", value=payload.site_tagline, actor_user_id=actor_user_id)
        self.repository.upsert(key="contact_email", value=payload.contact_email, actor_user_id=actor_user_id)
