from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.logger.repository import LoggerRepository


class LoggerService:
    def __init__(self, repository: LoggerRepository) -> None:
        self.repository = repository

    def write_request_log(
        self,
        *,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        level: str,
        duration_ms: float,
        message: str,
    ) -> None:
        self.repository.create(
            request_id=request_id,
            method=method,
            path=path,
            status_code=status_code,
            level=level,
            duration_ms=duration_ms,
            message=message,
        )

    def list_logs(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        q: str | None = None,
        level_filter: str | None = None,
        status_group: str | None = None,
        sort: str = "newest",
    ):
        safe_page = max(1, page)
        safe_per_page = min(max(1, per_page), 100)
        offset = (safe_page - 1) * safe_per_page
        safe_sort = sort if sort in {"newest", "oldest"} else "newest"
        safe_level = level_filter if level_filter in {"INFO", "WARNING", "ERROR"} else ""
        safe_status_group = status_group if status_group in {"2xx", "4xx", "5xx"} else ""
        items, total = self.repository.list_logs(
            offset=offset,
            limit=safe_per_page,
            q=q,
            level_filter=safe_level or None,
            status_group=safe_status_group or None,
            sort=safe_sort,
        )
        return items, total, safe_page, safe_per_page, safe_sort, safe_level, safe_status_group

    def delete_one(self, log_id: int) -> int:
        return self.repository.delete_one(log_id)

    def delete_many(self, log_ids: list[int]) -> int:
        return self.repository.delete_many(log_ids)

    def delete_page(
        self,
        *,
        page: int,
        per_page: int,
        q: str | None = None,
        level_filter: str | None = None,
        status_group: str | None = None,
        sort: str = "newest",
    ) -> int:
        safe_page = max(1, page)
        safe_per_page = min(max(1, per_page), 100)
        offset = (safe_page - 1) * safe_per_page
        safe_sort = sort if sort in {"newest", "oldest"} else "newest"
        safe_level = level_filter if level_filter in {"INFO", "WARNING", "ERROR"} else ""
        safe_status_group = status_group if status_group in {"2xx", "4xx", "5xx"} else ""
        page_ids = self.repository.list_ids_for_page(
            offset=offset,
            limit=safe_per_page,
            q=q,
            level_filter=safe_level or None,
            status_group=safe_status_group or None,
            sort=safe_sort,
        )
        return self.repository.delete_many(page_ids)

    def cleanup_retention(self, *, keep_days: int | None, max_rows: int | None) -> int:
        deleted_total = 0
        if keep_days is not None:
            safe_keep_days = max(0, keep_days)
            cutoff = datetime.now(timezone.utc) - timedelta(days=safe_keep_days)
            deleted_total += self.repository.delete_older_than(cutoff=cutoff)

        if max_rows is not None:
            safe_max_rows = max(1, max_rows)
            total_rows = self.repository.count_all()
            excess = total_rows - safe_max_rows
            if excess > 0:
                delete_ids = self.repository.list_oldest_ids(limit=excess)
                deleted_total += self.repository.delete_many(delete_ids)

        return deleted_total
