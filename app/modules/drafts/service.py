from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.modules.drafts.repository import DraftRepository
from app.modules.drafts.schemas import DraftOut, DraftRecentOut, DraftSaveResult


class DraftService:
    def __init__(self, repository: DraftRepository) -> None:
        self.repository = repository

    def get_draft(self, *, user_id: int, entity_type: str, entity_key: str) -> DraftOut | None:
        model = self.repository.get(user_id=user_id, entity_type=entity_type, entity_key=entity_key)
        if model is None:
            return None
        payload = json.loads(model.payload_json)
        return DraftOut(entity_type=model.entity_type, entity_key=model.entity_key, payload=payload, updated_at=model.updated_at)

    def save_draft(self, *, user_id: int, entity_type: str, entity_key: str, payload: dict[str, str]) -> DraftSaveResult:
        payload_json = json.dumps(payload, ensure_ascii=True)
        existing = self.repository.get(user_id=user_id, entity_type=entity_type, entity_key=entity_key)
        throttled = False

        if existing is not None:
            now = datetime.now(timezone.utc)
            updated_at = existing.updated_at
            if updated_at.tzinfo is None:
                now = now.replace(tzinfo=None)
            elapsed = (now - updated_at).total_seconds()
            if elapsed < settings.draft_min_save_interval_seconds and existing.payload_json == payload_json:
                throttled = True
                payload_existing = json.loads(existing.payload_json)
                return DraftSaveResult(
                    draft=DraftOut(
                        entity_type=existing.entity_type,
                        entity_key=existing.entity_key,
                        payload=payload_existing,
                        updated_at=existing.updated_at,
                    ),
                    throttled=throttled,
                )

        model = self.repository.upsert(
            user_id=user_id,
            entity_type=entity_type,
            entity_key=entity_key,
            payload_json=payload_json,
        )
        return DraftSaveResult(
            draft=DraftOut(
                entity_type=model.entity_type,
                entity_key=model.entity_key,
                payload=payload,
                updated_at=model.updated_at,
            ),
            throttled=throttled,
        )

    def discard_draft(self, *, user_id: int, entity_type: str, entity_key: str) -> None:
        self.repository.delete(user_id=user_id, entity_type=entity_type, entity_key=entity_key)

    def discard_many(self, *, user_id: int, pairs: list[tuple[str, str]]) -> int:
        return self.repository.delete_many(user_id=user_id, pairs=pairs)

    def cleanup_expired(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.draft_retention_days)
        return self.repository.delete_older_than(cutoff=cutoff)

    def list_recent(self, *, user_id: int, limit: int = 10, entity_type: str | None = None) -> list[DraftRecentOut]:
        models = self.repository.list_recent(user_id=user_id, limit=limit, entity_type=entity_type)
        return self._map_drafts(models)

    def list_for_user(self, *, user_id: int, limit: int = 100, entity_type: str | None = None, sort: str = "newest") -> list[DraftRecentOut]:
        models = self.repository.list_for_user(user_id=user_id, limit=limit, entity_type=entity_type, sort=sort)
        return self._map_drafts(models)

    def count_for_user(self, *, user_id: int) -> int:
        return self.repository.count_for_user(user_id=user_id)

    def _map_drafts(self, models) -> list[DraftRecentOut]:
        results: list[DraftRecentOut] = []
        for model in models:
            try:
                payload = json.loads(model.payload_json)
            except json.JSONDecodeError:
                payload = {}
            preview_title = str(payload.get("title") or payload.get("name") or payload.get("slug") or model.entity_key)
            results.append(
                DraftRecentOut(
                    entity_type=model.entity_type,
                    entity_key=model.entity_key,
                    updated_at=model.updated_at,
                    preview_title=preview_title[:120],
                )
            )
        return results
