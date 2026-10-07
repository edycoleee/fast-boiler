from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.modules.logger.models import RequestLog


class LoggerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        level: str,
        duration_ms: float,
        message: str,
    ) -> RequestLog:
        model = RequestLog(
            request_id=request_id,
            method=method,
            path=path,
            status_code=status_code,
            level=level,
            duration_ms=duration_ms,
            message=message,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def _apply_filters(
        self,
        query,
        *,
        q: str | None = None,
        level_filter: str | None = None,
        status_group: str | None = None,
    ):
        keyword = (q or "").strip()
        if keyword:
            like_pattern = f"%{keyword}%"
            query = query.where(or_(RequestLog.path.ilike(like_pattern), RequestLog.request_id.ilike(like_pattern), RequestLog.message.ilike(like_pattern)))

        if level_filter in {"INFO", "WARNING", "ERROR"}:
            query = query.where(RequestLog.level == level_filter)

        if status_group == "2xx":
            query = query.where(RequestLog.status_code >= 200, RequestLog.status_code < 300)
        elif status_group == "4xx":
            query = query.where(RequestLog.status_code >= 400, RequestLog.status_code < 500)
        elif status_group == "5xx":
            query = query.where(RequestLog.status_code >= 500, RequestLog.status_code < 600)
        return query

    def list_logs(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        q: str | None = None,
        level_filter: str | None = None,
        status_group: str | None = None,
        sort: str = "newest",
    ) -> tuple[list[RequestLog], int]:
        query = select(RequestLog)
        count_query = select(func.count()).select_from(RequestLog)
        query = self._apply_filters(query, q=q, level_filter=level_filter, status_group=status_group)
        count_query = self._apply_filters(count_query, q=q, level_filter=level_filter, status_group=status_group)
        if sort == "oldest":
            query = query.order_by(RequestLog.created_at.asc(), RequestLog.id.asc())
        else:
            query = query.order_by(RequestLog.created_at.desc(), RequestLog.id.desc())
        items = self.db.scalars(query.offset(offset).limit(limit)).all()
        total = self.db.scalar(count_query) or 0
        return items, int(total)

    def list_ids_for_page(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        q: str | None = None,
        level_filter: str | None = None,
        status_group: str | None = None,
        sort: str = "newest",
    ) -> list[int]:
        query = select(RequestLog.id)
        query = self._apply_filters(query, q=q, level_filter=level_filter, status_group=status_group)
        if sort == "oldest":
            query = query.order_by(RequestLog.created_at.asc(), RequestLog.id.asc())
        else:
            query = query.order_by(RequestLog.created_at.desc(), RequestLog.id.desc())
        rows = self.db.scalars(query.offset(offset).limit(limit)).all()
        return [int(item_id) for item_id in rows]

    def delete_one(self, log_id: int) -> int:
        result = self.db.execute(delete(RequestLog).where(RequestLog.id == log_id))
        self.db.commit()
        return int(result.rowcount or 0)

    def delete_many(self, log_ids: list[int]) -> int:
        if not log_ids:
            return 0
        result = self.db.execute(delete(RequestLog).where(RequestLog.id.in_(log_ids)))
        self.db.commit()
        return int(result.rowcount or 0)

    def count_all(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(RequestLog)) or 0)

    def list_oldest_ids(self, *, limit: int) -> list[int]:
        if limit <= 0:
            return []
        query = select(RequestLog.id).order_by(RequestLog.created_at.asc(), RequestLog.id.asc()).limit(limit)
        rows = self.db.scalars(query).all()
        return [int(item_id) for item_id in rows]

    def delete_older_than(self, *, cutoff: datetime) -> int:
        result = self.db.execute(delete(RequestLog).where(RequestLog.created_at <= cutoff))
        self.db.commit()
        return int(result.rowcount or 0)
