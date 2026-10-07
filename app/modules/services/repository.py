from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.services.models import ServiceItem
from app.modules.services.schemas import ServiceCreate, ServiceUpdate


class ServicesRepository:
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
    ) -> tuple[list[ServiceItem], int]:
        query = select(ServiceItem)
        count_query = select(func.count()).select_from(ServiceItem)

        keyword = (q or "").strip()
        if keyword:
            like_pattern = f"%{keyword}%"
            predicate = or_(ServiceItem.name.ilike(like_pattern), ServiceItem.slug.ilike(like_pattern), ServiceItem.summary.ilike(like_pattern))
            query = query.where(predicate)
            count_query = count_query.where(predicate)

        if status_filter in {"draft", "published"}:
            status_predicate = ServiceItem.status == status_filter
            query = query.where(status_predicate)
            count_query = count_query.where(status_predicate)

        order_map = {
            "created_desc": ServiceItem.created_at.desc(),
            "created_asc": ServiceItem.created_at.asc(),
            "name_asc": ServiceItem.name.asc(),
            "name_desc": ServiceItem.name.desc(),
        }
        order_by = order_map.get(sort, ServiceItem.created_at.desc())
        items = self.db.scalars(query.order_by(order_by).offset(offset).limit(limit)).all()
        total = self.db.scalar(count_query) or 0
        return items, int(total)

    def get_by_id(self, item_id: int) -> ServiceItem | None:
        return self.db.get(ServiceItem, item_id)

    def get_by_slug(self, slug: str) -> ServiceItem | None:
        return self.db.scalar(select(ServiceItem).where(ServiceItem.slug == slug))

    def create(self, payload: ServiceCreate, *, actor_user_id: int | None = None) -> ServiceItem:
        item = ServiceItem(
            name=payload.name,
            slug=payload.slug,
            summary=payload.summary,
            description=payload.description,
            status=payload.status,
            created_by=actor_user_id,
            updated_by=actor_user_id,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, model: ServiceItem, payload: ServiceUpdate, *, actor_user_id: int | None = None) -> ServiceItem:
        changed = payload.model_dump(exclude_unset=True)
        for key, value in changed.items():
            setattr(model, key, value)
        model.updated_by = actor_user_id
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, model: ServiceItem) -> None:
        self.db.delete(model)
        self.db.commit()
