from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.main import app
from app.modules.logger.models import RequestLog


def login_as_admin(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def _exists_request_id(request_id: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(RequestLog.id).filter(RequestLog.request_id == request_id).first() is not None
    finally:
        db.close()


def _ids_for_request_ids(request_ids: list[str]) -> list[int]:
    db = SessionLocal()
    try:
        rows = (
            db.query(RequestLog.id)
            .filter(RequestLog.request_id.in_(request_ids))
            .order_by(RequestLog.id.desc())
            .all()
        )
        return [int(row[0]) for row in rows]
    finally:
        db.close()


def test_logger_page_access_and_card_visible():
    with TestClient(app) as client:
        login_as_admin(client)
        dashboard = client.get("/admin")
        assert dashboard.status_code == 200
        assert "Logger Table" in dashboard.text

        page = client.get("/admin/logger")
        assert page.status_code == 200
        assert "Delete Selected" in page.text
        assert "Delete This Page" in page.text
        assert "Total (Filtered)" in page.text
        assert "INFO / 2xx" in page.text


def test_logger_delete_single_item():
    with TestClient(app) as client:
        login_as_admin(client)
        request_id = "logger-single-delete-case"
        client.get("/health", headers={"x-request-id": request_id})
        candidate_ids = _ids_for_request_ids([request_id])
        assert candidate_ids
        target_id = candidate_ids[0]

        response = client.post(
            "/admin/logger/delete",
            data={"log_id": target_id, "page": 1, "per_page": 20, "q": "", "sort": "newest"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "result=deleted" in response.headers["location"]
        assert _exists_request_id(request_id) is False


def test_logger_bulk_delete_selected():
    with TestClient(app) as client:
        login_as_admin(client)
        request_ids = ["logger-bulk-delete-a", "logger-bulk-delete-b"]
        client.get("/health", headers={"x-request-id": request_ids[0]})
        client.get("/health", headers={"x-request-id": request_ids[1]})
        target_ids = _ids_for_request_ids(request_ids)
        assert len(target_ids) >= 2

        response = client.post(
            "/admin/logger/bulk-delete",
            data={"log_ids": target_ids, "page": 1, "per_page": 20, "q": "", "sort": "newest"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "result=bulk-deleted" in response.headers["location"]
        for request_id in request_ids:
            assert _exists_request_id(request_id) is False


def test_logger_delete_current_page():
    with TestClient(app) as client:
        login_as_admin(client)
        request_ids = ["logger-page-delete-a", "logger-page-delete-b", "logger-page-delete-c"]
        client.get("/health", headers={"x-request-id": request_ids[0]})
        client.get("/health", headers={"x-request-id": request_ids[1]})
        client.get("/health", headers={"x-request-id": request_ids[2]})
        before_ids = _ids_for_request_ids(request_ids)
        assert before_ids

        response = client.post(
            "/admin/logger/delete-page",
            data={"page": 1, "per_page": 3, "q": "", "sort": "newest"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "result=page-deleted" in response.headers["location"]

        for request_id in request_ids:
            assert _exists_request_id(request_id) is False


def test_logger_filter_by_level_and_status_group():
    with TestClient(app) as client:
        login_as_admin(client)
        info_request_id = "logger-filter-info-200"
        warning_request_id = "logger-filter-warning-404"

        client.get("/health", headers={"x-request-id": info_request_id})
        client.get("/api/v1/news/999999", headers={"x-request-id": warning_request_id})

        info_page = client.get(
            "/admin/logger",
            params={"q": "logger-filter-", "level_filter": "INFO", "status_group": "2xx", "sort": "newest"},
        )
        assert info_page.status_code == 200
        assert info_request_id in info_page.text
        assert warning_request_id not in info_page.text

        warning_page = client.get(
            "/admin/logger",
            params={"q": "logger-filter-", "level_filter": "WARNING", "status_group": "4xx", "sort": "newest"},
        )
        assert warning_page.status_code == 200
        assert warning_request_id in warning_page.text


def test_logger_retention_cleanup_with_keep_days():
    with TestClient(app) as client:
        login_as_admin(client)
        request_ids = ["logger-retention-a", "logger-retention-b"]
        client.get("/health", headers={"x-request-id": request_ids[0]})
        client.get("/health", headers={"x-request-id": request_ids[1]})
        assert _exists_request_id(request_ids[0]) is True
        assert _exists_request_id(request_ids[1]) is True

        response = client.post(
            "/admin/logger/retention-cleanup",
            data={"keep_days": 0, "max_rows": "", "page": 1, "per_page": 20, "q": "", "sort": "newest"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "result=retention-cleaned" in response.headers["location"]
        assert "deleted_count=" in response.headers["location"]
        assert _exists_request_id(request_ids[0]) is False
        assert _exists_request_id(request_ids[1]) is False
