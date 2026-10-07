from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str
    updated_by: int | None
    updated_at: datetime


class SiteSettingsUpdate(BaseModel):
    site_name: str = Field(min_length=1, max_length=120)
    site_tagline: str = Field(min_length=1, max_length=180)
    contact_email: str = Field(min_length=3, max_length=180)
