from __future__ import annotations

from fastapi import HTTPException, status

from app.modules.services.repository import ServicesRepository
from app.modules.services.schemas import ServiceCreate, ServiceUpdate


class ServicesService:
    def __init__(self, repository: ServicesRepository) -> None:
        self.repository = repository

    def list_services(
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
        safe_sort = sort if sort in {"created_desc", "created_asc", "name_asc", "name_desc"} else "created_desc"
        safe_status = status_filter if status_filter in {"draft", "published"} else None
        items, total = self.repository.list_all(
            offset=offset,
            limit=safe_per_page,
            q=q,
            status_filter=safe_status,
            sort=safe_sort,
        )
        return items, total, safe_page, safe_per_page

    def list_services_for_export(
        self,
        *,
        q: str | None = None,
        status_filter: str | None = None,
        sort: str = "created_desc",
        max_items: int = 5000,
    ):
        safe_sort = sort if sort in {"created_desc", "created_asc", "name_asc", "name_desc"} else "created_desc"
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

    def get_service_by_id(self, item_id: int):
        item = self.repository.get_by_id(item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        return item

    def get_service_by_slug(self, slug: str):
        item = self.repository.get_by_slug(slug)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        return item

    def create_service(self, payload: ServiceCreate, *, actor_user_id: int | None = None):
        existing = self.repository.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        return self.repository.create(payload, actor_user_id=actor_user_id)

    def update_service(self, item_id: int, payload: ServiceUpdate, *, actor_user_id: int | None = None):
        model = self.get_service_by_id(item_id)
        if payload.slug and payload.slug != model.slug:
            existing = self.repository.get_by_slug(payload.slug)
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        return self.repository.update(model, payload, actor_user_id=actor_user_id)

    def delete_service(self, item_id: int) -> None:
        model = self.get_service_by_id(item_id)
        self.repository.delete(model)

    def duplicate_service(self, item_id: int, *, actor_user_id: int | None = None):
        source = self.get_service_by_id(item_id)
        duplicate_slug = self._build_duplicate_slug(source.slug)
        payload = ServiceCreate(
            name=f"{source.name} (Copy)",
            slug=duplicate_slug,
            summary=source.summary,
            description=source.description,
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
