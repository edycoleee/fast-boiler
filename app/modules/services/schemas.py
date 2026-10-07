from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    slug: str = Field(min_length=3, max_length=200)
    summary: str | None = Field(default=None, max_length=400)
    description: str = Field(min_length=10)
    status: str = Field(default="draft", pattern="^(draft|published)$")


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=200)
    slug: str | None = Field(default=None, min_length=3, max_length=200)
    summary: str | None = Field(default=None, max_length=400)
    description: str | None = Field(default=None, min_length=10)
    status: str | None = Field(default=None, pattern="^(draft|published)$")


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    summary: str | None
    description: str
    status: str
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime
