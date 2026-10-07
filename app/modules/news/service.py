from __future__ import annotations

from fastapi import HTTPException, status

from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import NewsCreate, NewsUpdate


class NewsService:
    def __init__(self, repository: NewsRepository) -> None:
        self.repository = repository

    def list_news(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
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
            q=q,
            status_filter=safe_status,
            sort=safe_sort,
        )
        return items, total, safe_page, safe_per_page

    def list_news_for_export(
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
            q=q,
            status_filter=safe_status,
            sort=safe_sort,
        )
        return items

    def get_news_by_id(self, news_id: int):
        model = self.repository.get_by_id(news_id)
        if model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
        return model

    def get_news_by_slug(self, slug: str):
        model = self.repository.get_by_slug(slug)
        if model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
        return model

    def create_news(self, payload: NewsCreate, *, actor_user_id: int | None = None):
        existing = self.repository.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        return self.repository.create(payload, actor_user_id=actor_user_id)

    def update_news(self, news_id: int, payload: NewsUpdate, *, actor_user_id: int | None = None):
        model = self.get_news_by_id(news_id)
        if payload.slug and payload.slug != model.slug:
            existing = self.repository.get_by_slug(payload.slug)
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        return self.repository.update(model, payload, actor_user_id=actor_user_id)

    def delete_news(self, news_id: int) -> None:
        model = self.get_news_by_id(news_id)
        self.repository.delete(model)

    def duplicate_news(self, news_id: int, *, actor_user_id: int | None = None):
        source = self.get_news_by_id(news_id)
        duplicate_slug = self._build_duplicate_slug(source.slug)
        payload = NewsCreate(
            title=f"{source.title} (Copy)",
            slug=duplicate_slug,
            excerpt=source.excerpt,
            content=source.content,
            status="draft",
        )
        return self.repository.create(payload, actor_user_id=actor_user_id)

    def _build_duplicate_slug(self, base_slug: str) -> str:
        candidate = f"{base_slug}-copy"
        index = 2
        while self.repository.get_by_slug(candidate) is not None:
            candidate = f"{base_slug}-copy-{index}"
            index += 1
        return candidate
