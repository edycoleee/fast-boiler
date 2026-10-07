from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.settings.models import AppSetting


class SettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[AppSetting]:
        return self.db.scalars(select(AppSetting).order_by(AppSetting.key.asc())).all()

    def get_by_key(self, key: str) -> AppSetting | None:
        return self.db.scalar(select(AppSetting).where(AppSetting.key == key))

    def upsert(self, *, key: str, value: str, actor_user_id: int | None = None) -> AppSetting:
        model = self.get_by_key(key)
        if model is None:
            model = AppSetting(key=key, value=value, updated_by=actor_user_id)
        else:
            model.value = value
            model.updated_by = actor_user_id
            model.updated_at = datetime.now(timezone.utc)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
