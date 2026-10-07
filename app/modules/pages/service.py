from __future__ import annotations

from fastapi import HTTPException, status

from app.modules.pages.repository import PagesRepository
from app.modules.pages.schemas import PageCreate, PageUpdate


class PagesService:
    def __init__(self, repository: PagesRepository) -> None:
        self.repository = repository

    def list_pages(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        published_only: bool = False,
        q: str | None = None,
        status_filter: str | None = None,
        sort: str = "created_desc",
    ):
        safe_page = max(1, page)
        safe_per_page = min(max(1, per_page), 100)
        offset = (safe_page - 1) * safe_per_page
        safe_sort = sort if sort in {"created_desc", "created_asc", "title_asc", "title_desc"} else "created_desc"
        safe_status = status_filter if status_filter in {"draft", "published"} else None
        items, total = self.repository.list_all(
            offset=offset,
            limit=safe_per_page,
            published_only=published_only,
            q=q,
            status_filter=safe_status,
            sort=safe_sort,
        )
        return items, total, safe_page, safe_per_page

    def list_pages_for_export(
        self,
        *,
        q: str | None = None,
        status_filter: str | None = None,
        sort: str = "created_desc",
        max_items: int = 5000,
    ):
        safe_sort = sort if sort in {"created_desc", "created_asc", "title_asc", "title_desc"} else "created_desc"
        safe_status = status_filter if status_filter in {"draft", "published"} else None
        safe_limit = min(max(1, max_items), 10000)
        items, _total = self.repository.list_all(
            offset=0,
            limit=safe_limit,
            published_only=False,
            q=q,
            status_filter=safe_status,
            sort=safe_sort,
        )
        return items

    def get_page_by_id(self, page_id: int):
        item = self.repository.get_by_id(page_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
        return item

    def get_page_by_slug(self, slug: str, *, published_only: bool = False):
        item = self.repository.get_by_slug(slug, published_only=published_only)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
        return item

    def create_page(self, payload: PageCreate, *, actor_user_id: int | None = None):
        existing = self.repository.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        return self.repository.create(payload, actor_user_id=actor_user_id)

    def update_page(self, page_id: int, payload: PageUpdate, *, actor_user_id: int | None = None):
        model = self.get_page_by_id(page_id)
        if payload.slug and payload.slug != model.slug:
            existing = self.repository.get_by_slug(payload.slug)
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        return self.repository.update(model, payload, actor_user_id=actor_user_id)

    def delete_page(self, page_id: int) -> None:
        model = self.get_page_by_id(page_id)
        self.repository.delete(model)
