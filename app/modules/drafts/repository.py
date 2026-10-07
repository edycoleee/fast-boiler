from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.drafts.models import Draft


class DraftRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, *, user_id: int, entity_type: str, entity_key: str) -> Draft | None:
        return self.db.scalar(
            select(Draft).where(
                Draft.user_id == user_id,
                Draft.entity_type == entity_type,
                Draft.entity_key == entity_key,
            )
        )

    def upsert(self, *, user_id: int, entity_type: str, entity_key: str, payload_json: str) -> Draft:
        model = self.get(user_id=user_id, entity_type=entity_type, entity_key=entity_key)
        if model is None:
            model = Draft(user_id=user_id, entity_type=entity_type, entity_key=entity_key, payload_json=payload_json)
        else:
            model.payload_json = payload_json
            model.updated_at = datetime.now(timezone.utc)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def list_recent(self, *, user_id: int, limit: int = 10, entity_type: str | None = None) -> list[Draft]:
        query = select(Draft).where(Draft.user_id == user_id)
        if entity_type:
            query = query.where(Draft.entity_type == entity_type)
        query = query.order_by(Draft.updated_at.desc()).limit(limit)
        return self.db.scalars(query).all()

    def list_for_user(self, *, user_id: int, limit: int = 100, entity_type: str | None = None, sort: str = "newest") -> list[Draft]:
        query = select(Draft).where(Draft.user_id == user_id)
        if entity_type:
            query = query.where(Draft.entity_type == entity_type)
        if sort == "oldest":
            query = query.order_by(Draft.updated_at.asc(), Draft.id.asc())
        else:
            query = query.order_by(Draft.updated_at.desc(), Draft.id.desc())
        query = query.limit(limit)
        return self.db.scalars(query).all()

    def count_for_user(self, *, user_id: int) -> int:
        count = self.db.scalar(select(func.count()).select_from(Draft).where(Draft.user_id == user_id))
        return int(count or 0)

    def delete(self, *, user_id: int, entity_type: str, entity_key: str) -> None:
        self.db.execute(
            delete(Draft).where(
                Draft.user_id == user_id,
                Draft.entity_type == entity_type,
                Draft.entity_key == entity_key,
            )
        )
        self.db.commit()

    def delete_many(self, *, user_id: int, pairs: list[tuple[str, str]]) -> int:
        deleted = 0
        for entity_type, entity_key in pairs:
            result = self.db.execute(
                delete(Draft).where(
                    Draft.user_id == user_id,
                    Draft.entity_type == entity_type,
                    Draft.entity_key == entity_key,
                )
            )
            deleted += int(result.rowcount or 0)
        self.db.commit()
        return deleted

    def delete_older_than(self, cutoff: datetime) -> int:
        result = self.db.execute(delete(Draft).where(Draft.updated_at < cutoff))
        self.db.commit()
        return int(result.rowcount or 0)
