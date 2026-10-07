from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.news.models import News
from app.modules.news.schemas import NewsCreate, NewsUpdate


class NewsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        q: str | None = None,
        status_filter: str | None = None,
        sort: str = "created_desc",
    ) -> tuple[list[News], int]:
        query = select(News)
        count_query = select(func.count()).select_from(News)

        keyword = (q or "").strip()
        if keyword:
            like_pattern = f"%{keyword}%"
            predicate = or_(News.title.ilike(like_pattern), News.slug.ilike(like_pattern), News.excerpt.ilike(like_pattern))
            query = query.where(predicate)
            count_query = count_query.where(predicate)

        if status_filter in {"draft", "published"}:
            status_predicate = News.status == status_filter
            query = query.where(status_predicate)
            count_query = count_query.where(status_predicate)

        order_map = {
            "created_desc": News.created_at.desc(),
            "created_asc": News.created_at.asc(),
            "title_asc": News.title.asc(),
            "title_desc": News.title.desc(),
        }
        order_by = order_map.get(sort, News.created_at.desc())
        items = self.db.scalars(query.order_by(order_by).offset(offset).limit(limit)).all()
        total = self.db.scalar(count_query) or 0
        return items, int(total)

    def get_by_id(self, news_id: int) -> News | None:
        return self.db.get(News, news_id)

    def get_by_slug(self, slug: str) -> News | None:
        return self.db.scalar(select(News).where(News.slug == slug))

    def create(self, payload: NewsCreate, *, actor_user_id: int | None = None) -> News:
        model = News(
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt,
            content=payload.content,
            status=payload.status,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def update(self, model: News, payload: NewsUpdate, *, actor_user_id: int | None = None) -> News:
        changed = payload.model_dump(exclude_unset=True)
        for key, value in changed.items():
            setattr(model, key, value)
        model.updated_by = actor_user_id
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, model: News) -> None:
        self.db.delete(model)
        self.db.commit()
