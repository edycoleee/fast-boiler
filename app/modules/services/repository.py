from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.services.models import ServiceItem
from app.modules.services.schemas import ServiceCreate, ServiceUpdate


class ServicesRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self, *, offset: int = 0, limit: int = 20) -> tuple[list[ServiceItem], int]:
        items = self.db.scalars(select(ServiceItem).order_by(ServiceItem.created_at.desc()).offset(offset).limit(limit)).all()
        total = self.db.scalar(select(func.count()).select_from(ServiceItem)) or 0
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
