from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class NewsCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    slug: str = Field(min_length=3, max_length=200)
    excerpt: str | None = Field(default=None, max_length=400)
    content: str = Field(min_length=10)
    status: str = Field(default="draft", pattern="^(draft|published)$")


class NewsUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    slug: str | None = Field(default=None, min_length=3, max_length=200)
    excerpt: str | None = Field(default=None, max_length=400)
    content: str | None = Field(default=None, min_length=10)
    status: str | None = Field(default=None, pattern="^(draft|published)$")


class NewsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    excerpt: str | None
    content: str
    status: str
    created_by: int | None
    updated_by: int | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApiMeta(BaseModel):
    request_id: str
    timestamp: datetime
    page: int | None = None
    per_page: int | None = None
    total: int | None = None


class ApiError(BaseModel):
    code: str
    details: list[dict[str, str]] | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None
    error: ApiError | None = None
    meta: ApiMeta
