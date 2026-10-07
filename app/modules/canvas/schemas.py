from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CanvasSavePayload(BaseModel):
    document_key: str = Field(default="default", min_length=1, max_length=80)
    title: str = Field(default="Untitled Canvas", min_length=1, max_length=120)
    payload: dict[str, Any]
    last_known_updated_at: datetime | None = None
    force: bool = False


class CanvasDocumentOut(BaseModel):
    document_key: str
    title: str
    payload: dict[str, Any]
    updated_at: datetime


class CanvasDocumentSummaryOut(BaseModel):
    document_key: str
    title: str
    updated_at: datetime


class CanvasRenamePayload(BaseModel):
    document_key: str = Field(min_length=1, max_length=80)
    new_document_key: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=120)
