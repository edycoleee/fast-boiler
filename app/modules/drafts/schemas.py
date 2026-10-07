from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DraftAutosavePayload(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_key: str = Field(min_length=1, max_length=120)
    payload: dict[str, str]


class DraftOut(BaseModel):
    entity_type: str
    entity_key: str
    payload: dict[str, str]
    updated_at: datetime


class DraftSaveResult(BaseModel):
    draft: DraftOut
    throttled: bool


class DraftRecentOut(BaseModel):
    entity_type: str
    entity_key: str
    updated_at: datetime
    preview_title: str
