from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.pages.models import Page
from app.modules.pages.schemas import PageCreate, PageUpdate


class PagesRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        published_only: bool = False,
        q: str | None = None,
        status_filter: str | None = None,
        sort: str = "created_desc",
    ) -> tuple[list[Page], int]:
        query = select(Page)
        count_query = select(func.count()).select_from(Page)
        keyword = (q or "").strip()
        if keyword:
            like_pattern = f"%{keyword}%"
            predicate = or_(Page.title.ilike(like_pattern), Page.slug.ilike(like_pattern), Page.summary.ilike(like_pattern))
            query = query.where(predicate)
            count_query = count_query.where(predicate)
        if published_only:
            query = query.where(Page.status == "published")
            count_query = count_query.where(Page.status == "published")
        elif status_filter in {"draft", "published"}:
            status_predicate = Page.status == status_filter
            query = query.where(status_predicate)
            count_query = count_query.where(status_predicate)

        order_map = {
            "created_desc": Page.created_at.desc(),
            "created_asc": Page.created_at.asc(),
            "title_asc": Page.title.asc(),
            "title_desc": Page.title.desc(),
        }
        order_by = order_map.get(sort, Page.created_at.desc())
        items = self.db.scalars(query.order_by(order_by).offset(offset).limit(limit)).all()
        total = self.db.scalar(count_query) or 0
        return items, int(total)

    def get_by_id(self, page_id: int) -> Page | None:
        return self.db.get(Page, page_id)

    def get_by_slug(self, slug: str, *, published_only: bool = False) -> Page | None:
        query = select(Page).where(Page.slug == slug)
        if published_only:
            query = query.where(Page.status == "published")
        return self.db.scalar(query)

    def create(self, payload: PageCreate, *, actor_user_id: int | None = None) -> Page:
        model = Page(
            title=payload.title,
            slug=payload.slug,
            summary=payload.summary,
            content=payload.content,
            status=payload.status,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def update(self, model: Page, payload: PageUpdate, *, actor_user_id: int | None = None) -> Page:
        changed = payload.model_dump(exclude_unset=True)
        for key, value in changed.items():
            setattr(model, key, value)
        model.updated_by = actor_user_id
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, model: Page) -> None:
        self.db.delete(model)
        self.db.commit()
