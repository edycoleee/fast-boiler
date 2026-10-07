from __future__ import annotations

from pydantic import BaseModel


class MediaUploadResult(BaseModel):
    original_name: str
    stored_name: str
    content_type: str
    size: int
    path: str

