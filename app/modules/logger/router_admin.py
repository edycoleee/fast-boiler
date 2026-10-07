from __future__ import annotations

from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.excel import excel_response
from app.core.templates import templates
from app.modules.auth.dependencies import require_permission
from app.modules.logger.repository import LoggerRepository
from app.modules.logger.service import LoggerService

router = APIRouter(
    prefix="/admin/logger",
    tags=["logger-admin"],
    dependencies=[Depends(require_permission("logger.manage"))],
)


def get_service(db: Session = Depends(get_db)) -> LoggerService:
    return LoggerService(LoggerRepository(db))


def _build_query_tail(*, page: int, per_page: int, q: str, level_filter: str, status_group: str, sort: str) -> str:
    return (
        f"page={page}&per_page={per_page}&q={quote_plus(q)}"
        f"&level_filter={quote_plus(level_filter)}&status_group={quote_plus(status_group)}&sort={quote_plus(sort)}"
    )


def _parse_optional_positive_int(raw: str) -> int | None:
    value = (raw or "").strip()
    if not value:
        return None
    parsed = int(value)
    if parsed < 0:
        raise ValueError("value must be >= 0")
    return parsed


@router.get("")
def logger_index(
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    q: str = Query(default=""),
    level_filter: str = Query(default=""),
    status_group: str = Query(default=""),
    sort: str = Query(default="newest"),
    result: str | None = Query(default=None),
    deleted_count: int | None = Query(default=None),
    keep_days_q: str = Query(default=""),
    max_rows_q: str = Query(default=""),
    service: LoggerService = Depends(get_service),
):
    items, total, page, per_page, safe_sort, safe_level, safe_status_group = service.list_logs(
        page=page,
        per_page=per_page,
        q=q,
        level_filter=level_filter,
        status_group=status_group,
        sort=sort,
    )
    return templates.TemplateResponse(
        request=request,
        name="admin/logger/index.html",
        context={
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "q": q,
            "level_filter": safe_level,
            "status_group": safe_status_group,
            "sort": safe_sort,
            "result": result,
            "deleted_count": deleted_count,
            "keep_days_q": keep_days_q,
            "max_rows_q": max_rows_q,
        },
    )


@router.get("/export.xlsx")
def logger_export(
    q: str = Query(default=""),
    level_filter: str = Query(default=""),
    status_group: str = Query(default=""),
    sort: str = Query(default="newest"),
    service: LoggerService = Depends(get_service),
):
    items = service.list_logs_for_export(
        q=q,
        level_filter=level_filter or None,
        status_group=status_group or None,
        sort=sort,
    )
    rows = [
        [
            item.id,
            item.created_at.isoformat(),
            item.request_id,
            item.method,
            item.path,
            item.status_code,
            item.level,
            float(item.duration_ms),
            item.message,
        ]
        for item in items
    ]
    return excel_response(
        filename_prefix="logger-export",
        sheet_name="RequestLogs",
        headers=["ID", "Time", "Request ID", "Method", "Path", "Status Code", "Level", "Duration (ms)", "Message"],
        rows=rows,
    )


@router.post("/delete")
def logger_delete_one(
    log_id: int = Form(...),
    page: int = Form(default=1),
    per_page: int = Form(default=20),
    q: str = Form(default=""),
    level_filter: str = Form(default=""),
    status_group: str = Form(default=""),
    sort: str = Form(default="newest"),
    service: LoggerService = Depends(get_service),
):
    deleted = service.delete_one(log_id)
    result = "deleted" if deleted else "not-found"
    tail = _build_query_tail(
        page=page,
        per_page=per_page,
        q=q,
        level_filter=level_filter,
        status_group=status_group,
        sort=sort,
    )
    return RedirectResponse(url=f"/admin/logger?{tail}&result={result}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/bulk-delete")
def logger_bulk_delete(
    log_ids: list[int] = Form(default=[]),
    page: int = Form(default=1),
    per_page: int = Form(default=20),
    q: str = Form(default=""),
    level_filter: str = Form(default=""),
    status_group: str = Form(default=""),
    sort: str = Form(default="newest"),
    service: LoggerService = Depends(get_service),
):
    deleted = service.delete_many(log_ids)
    result = "bulk-deleted" if deleted > 0 else "bulk-empty"
    tail = _build_query_tail(
        page=page,
        per_page=per_page,
        q=q,
        level_filter=level_filter,
        status_group=status_group,
        sort=sort,
    )
    return RedirectResponse(url=f"/admin/logger?{tail}&result={result}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/delete-page")
def logger_delete_page(
    page: int = Form(default=1),
    per_page: int = Form(default=20),
    q: str = Form(default=""),
    level_filter: str = Form(default=""),
    status_group: str = Form(default=""),
    sort: str = Form(default="newest"),
    service: LoggerService = Depends(get_service),
):
    deleted = service.delete_page(
        page=page,
        per_page=per_page,
        q=q,
        level_filter=level_filter,
        status_group=status_group,
        sort=sort,
    )
    result = "page-deleted" if deleted > 0 else "page-empty"
    tail = _build_query_tail(
        page=1,
        per_page=per_page,
        q=q,
        level_filter=level_filter,
        status_group=status_group,
        sort=sort,
    )
    return RedirectResponse(url=f"/admin/logger?{tail}&result={result}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/retention-cleanup")
def logger_retention_cleanup(
    keep_days: str = Form(default=""),
    max_rows: str = Form(default=""),
    page: int = Form(default=1),
    per_page: int = Form(default=20),
    q: str = Form(default=""),
    level_filter: str = Form(default=""),
    status_group: str = Form(default=""),
    sort: str = Form(default="newest"),
    service: LoggerService = Depends(get_service),
):
    try:
        parsed_keep_days = _parse_optional_positive_int(keep_days)
        parsed_max_rows = _parse_optional_positive_int(max_rows)
    except ValueError:
        tail = _build_query_tail(
            page=page,
            per_page=per_page,
            q=q,
            level_filter=level_filter,
            status_group=status_group,
            sort=sort,
        )
        return RedirectResponse(url=f"/admin/logger?{tail}&result=retention-invalid", status_code=status.HTTP_303_SEE_OTHER)

    if parsed_keep_days is None and parsed_max_rows is None:
        tail = _build_query_tail(
            page=page,
            per_page=per_page,
            q=q,
            level_filter=level_filter,
            status_group=status_group,
            sort=sort,
        )
        return RedirectResponse(url=f"/admin/logger?{tail}&result=retention-empty", status_code=status.HTTP_303_SEE_OTHER)

    deleted = service.cleanup_retention(keep_days=parsed_keep_days, max_rows=parsed_max_rows)
    tail = _build_query_tail(
        page=1,
        per_page=per_page,
        q=q,
        level_filter=level_filter,
        status_group=status_group,
        sort=sort,
    )
    return RedirectResponse(
        url=(
            f"/admin/logger?{tail}&result=retention-cleaned&deleted_count={deleted}"
            f"&keep_days_q={quote_plus(keep_days)}&max_rows_q={quote_plus(max_rows)}"
        ),
        status_code=status.HTTP_303_SEE_OTHER,
    )
