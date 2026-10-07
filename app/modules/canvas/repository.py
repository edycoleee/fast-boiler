from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.canvas.models import CanvasDocument


class CanvasRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, *, user_id: int, document_key: str) -> CanvasDocument | None:
        return self.db.scalar(
            select(CanvasDocument).where(
                CanvasDocument.user_id == user_id,
                CanvasDocument.document_key == document_key,
            )
        )

    def upsert(self, *, user_id: int, document_key: str, title: str, payload_json: str) -> CanvasDocument:
        model = self.get(user_id=user_id, document_key=document_key)
        if model is None:
            model = CanvasDocument(
                user_id=user_id,
                document_key=document_key,
                title=title,
                payload_json=payload_json,
            )
        else:
            model.title = title
            model.payload_json = payload_json
            model.updated_at = datetime.now(timezone.utc)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def list_for_user(self, *, user_id: int, limit: int = 50) -> list[CanvasDocument]:
        query = (
            select(CanvasDocument)
            .where(CanvasDocument.user_id == user_id)
            .order_by(CanvasDocument.updated_at.desc(), CanvasDocument.id.desc())
            .limit(limit)
        )
        return self.db.scalars(query).all()

    def delete_document(self, *, user_id: int, document_key: str) -> bool:
        result = self.db.execute(
            delete(CanvasDocument).where(
                CanvasDocument.user_id == user_id,
                CanvasDocument.document_key == document_key,
            )
        )
        self.db.commit()
        return int(result.rowcount or 0) > 0

    def rename_document(
        self,
        *,
        user_id: int,
        document_key: str,
        new_document_key: str,
        new_title: str,
    ) -> CanvasDocument | None:
        model = self.get(user_id=user_id, document_key=document_key)
        if model is None:
            return None
        existing_target = self.get(user_id=user_id, document_key=new_document_key)
        if existing_target is not None and existing_target.id != model.id:
            raise ValueError("Target document key already exists")
        model.document_key = new_document_key
        model.title = new_title
        model.updated_at = datetime.now(timezone.utc)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
