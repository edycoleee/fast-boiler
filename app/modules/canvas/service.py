from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.modules.canvas.repository import CanvasRepository
from app.modules.canvas.schemas import CanvasDocumentOut, CanvasDocumentSummaryOut


class CanvasService:
    def __init__(self, repository: CanvasRepository) -> None:
        self.repository = repository

    def save_document(self, *, user_id: int, document_key: str, title: str, payload: dict[str, Any]) -> CanvasDocumentOut:
        payload_json = json.dumps(payload, ensure_ascii=False)
        model = self.repository.upsert(
            user_id=user_id,
            document_key=document_key,
            title=title,
            payload_json=payload_json,
        )
        return CanvasDocumentOut(
            document_key=model.document_key,
            title=model.title,
            payload=payload,
            updated_at=model.updated_at,
        )

    def save_document_with_conflict_guard(
        self,
        *,
        user_id: int,
        document_key: str,
        title: str,
        payload: dict[str, Any],
        last_known_updated_at: datetime | None,
        force: bool,
    ) -> CanvasDocumentOut:
        current = self.repository.get(user_id=user_id, document_key=document_key)
        if current is not None and not force and last_known_updated_at is not None and current.updated_at > last_known_updated_at:
            raise ValueError("Canvas document has newer changes on server")
        return self.save_document(
            user_id=user_id,
            document_key=document_key,
            title=title,
            payload=payload,
        )

    def get_document(self, *, user_id: int, document_key: str) -> CanvasDocumentOut | None:
        model = self.repository.get(user_id=user_id, document_key=document_key)
        if model is None:
            return None
        payload = self._parse_payload(model.payload_json)
        return CanvasDocumentOut(
            document_key=model.document_key,
            title=model.title,
            payload=payload,
            updated_at=model.updated_at,
        )

    def list_documents(self, *, user_id: int, limit: int = 50) -> list[CanvasDocumentSummaryOut]:
        models = self.repository.list_for_user(user_id=user_id, limit=limit)
        return [
            CanvasDocumentSummaryOut(
                document_key=model.document_key,
                title=model.title,
                updated_at=model.updated_at,
            )
            for model in models
        ]

    def delete_document(self, *, user_id: int, document_key: str) -> bool:
        return self.repository.delete_document(user_id=user_id, document_key=document_key)

    def rename_document(
        self,
        *,
        user_id: int,
        document_key: str,
        new_document_key: str,
        title: str,
    ) -> CanvasDocumentSummaryOut | None:
        model = self.repository.rename_document(
            user_id=user_id,
            document_key=document_key,
            new_document_key=new_document_key,
            new_title=title,
        )
        if model is None:
            return None
        return CanvasDocumentSummaryOut(
            document_key=model.document_key,
            title=model.title,
            updated_at=model.updated_at,
        )

    def _parse_payload(self, payload_json: str) -> dict[str, Any]:
        try:
            parsed = json.loads(payload_json)
        except json.JSONDecodeError:
            return {"background": "#ffffff", "items": []}
        if not isinstance(parsed, dict):
            return {"background": "#ffffff", "items": []}
        if "items" not in parsed or not isinstance(parsed["items"], list):
            parsed["items"] = []
        if "background" not in parsed or not isinstance(parsed["background"], str):
            parsed["background"] = "#ffffff"
        return parsed
