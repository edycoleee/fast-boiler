from fastapi.testclient import TestClient
from uuid import uuid4

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService


def login_as_admin(client: TestClient) -> None:
    login_response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/admin"


def ensure_editor_user() -> None:
    db = SessionLocal()
    try:
        repo = AuthRepository(db)
        service = AuthService(repo)
        service.ensure_default_rbac()
        if repo.get_by_username("editor") is None:
            repo.create_user(username="editor", password_hash=hash_password("editor123"), role_name="editor")
    finally:
        db.close()


def login_as_editor(client: TestClient) -> None:
    ensure_editor_user()
    login_response = client.post(
        "/auth/login",
        data={"username": "editor", "password": "editor123"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/admin"


def test_admin_requires_login():
    with TestClient(app) as client:
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/auth/login"


def test_login_and_access_admin_pages():
    with TestClient(app) as client:
        login_as_admin(client)

        dashboard_response = client.get("/admin")
        assert dashboard_response.status_code == 200

        news_response = client.get("/admin/news")
        assert news_response.status_code == 200
        assert "Table utilities tersedia" in news_response.text

        news_create_response = client.get("/admin/news/new")
        assert news_create_response.status_code == 200
        assert "Breadcrumb" in news_create_response.text

        services_response = client.get("/admin/services")
        assert services_response.status_code == 200
        assert "Table utilities tersedia" in services_response.text

        services_create_response = client.get("/admin/services/new")
        assert services_create_response.status_code == 200
        assert "Breadcrumb" in services_create_response.text

        drafts_response = client.get("/admin/drafts")
        assert drafts_response.status_code == 200

        media_response = client.get("/admin/media")
        assert media_response.status_code == 200

        canvas_response = client.get("/admin/canvas")
        assert canvas_response.status_code == 200
        canvas_mode2_response = client.get("/admin/canvas/mode-2")
        assert canvas_mode2_response.status_code == 200
        assert "Regions JSON" in canvas_mode2_response.text
        assert "Undo" in canvas_mode2_response.text
        assert "Preview Region Only" in canvas_mode2_response.text
        assert "Download Preview PNG" in canvas_mode2_response.text

        logger_response = client.get("/admin/logger")
        assert logger_response.status_code == 200

        pages_response = client.get("/admin/pages")
        assert pages_response.status_code == 200

        settings_response = client.get("/admin/settings")
        assert settings_response.status_code == 200
        assert "Branding Guidance" in settings_response.text


def test_admin_excel_exports_available():
    with TestClient(app) as client:
        login_as_admin(client)
        export_urls = [
            "/admin/news/export.xlsx",
            "/admin/services/export.xlsx",
            "/admin/drafts/export.xlsx",
            "/admin/export/recent-drafts.xlsx",
            "/admin/export/recent-canvas.xlsx",
        ]
        for url in export_urls:
            response = client.get(url)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


def test_news_admin_prg_create_redirect():
    with TestClient(app) as client:
        login_as_admin(client)
        slug = f"news-{uuid4().hex[:8]}"
        response = client.post(
            "/admin/news",
            data={
                "title": "PRG News Test",
                "slug": slug,
                "excerpt": "excerpt",
                "content": "Konten valid untuk testing PRG.",
                "status": "draft",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/news?result=created"


def test_news_admin_prg_update_and_delete_redirect():
    with TestClient(app) as client:
        login_as_admin(client)
        slug = f"news-update-delete-{uuid4().hex[:8]}"
        create_response = client.post(
            "/admin/news",
            data={
                "title": "PRG News Update Delete",
                "slug": slug,
                "excerpt": "excerpt",
                "content": "Konten valid untuk testing update delete PRG.",
                "status": "draft",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303

        list_response = client.get("/api/v1/news")
        assert list_response.status_code == 200
        items = list_response.json()["data"]
        created = next(item for item in items if item["slug"] == slug)
        news_id = created["id"]

        update_response = client.post(
            f"/admin/news/{news_id}",
            data={
                "title": "PRG News Updated",
                "slug": slug,
                "excerpt": "updated",
                "content": "Konten telah diupdate untuk testing PRG.",
                "status": "published",
            },
            follow_redirects=False,
        )
        assert update_response.status_code == 303
        assert update_response.headers["location"] == "/admin/news?result=updated"

        delete_response = client.post(f"/admin/news/{news_id}/delete", follow_redirects=False)
        assert delete_response.status_code == 303
        assert delete_response.headers["location"] == "/admin/news?result=deleted"


def test_news_admin_duplicate_redirect_and_created_copy():
    with TestClient(app) as client:
        login_as_admin(client)
        slug = f"news-duplicate-{uuid4().hex[:8]}"
        create_response = client.post(
            "/admin/news",
            data={
                "title": "News Duplicate Source",
                "slug": slug,
                "excerpt": "excerpt",
                "content": "Konten valid untuk testing duplicate.",
                "status": "published",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303

        list_response = client.get("/api/v1/news")
        items = list_response.json()["data"]
        source = next(item for item in items if item["slug"] == slug)

        duplicate_response = client.post(f"/admin/news/{source['id']}/duplicate", follow_redirects=False)
        assert duplicate_response.status_code == 303
        assert duplicate_response.headers["location"] == "/admin/news?result=duplicated"

        list_after = client.get("/api/v1/news").json()["data"]
        duplicated = next(item for item in list_after if item["slug"].startswith(f"{slug}-copy"))
        assert duplicated["status"] == "draft"


def test_news_admin_pagination_and_audit_fields():
    with TestClient(app) as client:
        login_as_admin(client)
        created_slugs: list[str] = []
        for idx in range(12):
            slug = f"news-paginate-{idx}-{uuid4().hex[:6]}"
            created_slugs.append(slug)
            response = client.post(
                "/admin/news",
                data={
                    "title": f"News {idx}",
                    "slug": slug,
                    "excerpt": "excerpt",
                    "content": "Konten valid untuk pagination dan audit field.",
                    "status": "draft",
                },
                follow_redirects=False,
            )
            assert response.status_code == 303

        page_two = client.get("/api/v1/news", params={"page": 2, "per_page": 5})
        assert page_two.status_code == 200
        body = page_two.json()
        assert body["meta"]["page"] == 2
        assert body["meta"]["per_page"] == 5
        assert len(body["data"]) == 5

        first_created_slug = created_slugs[0]
        created_item = next(item for item in client.get("/api/v1/news").json()["data"] if item["slug"] == first_created_slug)
        assert created_item["created_by"] is not None
        assert created_item["updated_by"] is not None

        admin_page = client.get("/admin/news", params={"page": 2, "per_page": 5})
        assert admin_page.status_code == 200
        assert "Page" in admin_page.text


def test_news_htmx_table_partial_response():
    with TestClient(app) as client:
        login_as_admin(client)
        response = client.get(
            "/admin/news/partials/table",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert "<table" in response.text or "No news found." in response.text


def test_news_admin_filter_sort_search():
    with TestClient(app) as client:
        login_as_admin(client)
        unique_suffix = uuid4().hex[:6]
        draft_slug = f"news-filter-draft-{unique_suffix}"
        published_slug = f"news-filter-pub-{unique_suffix}"

        create_draft = client.post(
            "/admin/news",
            data={
                "title": f"Alpha Draft {unique_suffix}",
                "slug": draft_slug,
                "excerpt": "draft excerpt",
                "content": "Konten draft untuk validasi filter status news.",
                "status": "draft",
            },
            follow_redirects=False,
        )
        assert create_draft.status_code == 303

        create_published = client.post(
            "/admin/news",
            data={
                "title": f"Zulu Published {unique_suffix}",
                "slug": published_slug,
                "excerpt": "published excerpt",
                "content": "Konten published untuk validasi search dan sort news.",
                "status": "published",
            },
            follow_redirects=False,
        )
        assert create_published.status_code == 303

        filtered = client.get(
            "/admin/news/partials/table",
            params={"q": unique_suffix, "status_filter": "published", "sort": "title_desc", "per_page": 20},
            headers={"HX-Request": "true"},
        )
        assert filtered.status_code == 200
        assert published_slug in filtered.text
        assert draft_slug not in filtered.text


def test_news_htmx_form_inline_validation_error():
    with TestClient(app) as client:
        login_as_admin(client)
        response = client.post(
            "/admin/news",
            data={
                "title": "Bad News",
                "slug": f"bad-news-{uuid4().hex[:6]}",
                "excerpt": "bad",
                "content": "short",
                "status": "draft",
            },
            headers={"HX-Request": "true"},
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "Validation failed" in response.text


def test_services_api_list_shape():
    with TestClient(app) as client:
        response = client.get("/api/v1/services")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert "data" in payload
        assert "meta" in payload


def test_services_detail_not_found_page():
    with TestClient(app) as client:
        response = client.get("/services/slug-yang-tidak-ada")
        assert response.status_code == 404


def test_services_api_crud_cycle():
    with TestClient(app) as client:
        slug = f"services-api-cycle-{uuid4().hex[:8]}"
        create_response = client.post(
            "/api/v1/services",
            json={
                "name": "Services API Cycle",
                "slug": slug,
                "summary": "Cycle summary",
                "description": "Deskripsi API cycle untuk create update delete.",
                "status": "draft",
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()["data"]
        item_id = created["id"]

        get_response = client.get(f"/api/v1/services/{item_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["slug"] == slug

        update_response = client.put(
            f"/api/v1/services/{item_id}",
            json={
                "name": "Services API Cycle Updated",
                "status": "published",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["name"] == "Services API Cycle Updated"

        delete_response = client.delete(f"/api/v1/services/{item_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        not_found_response = client.get(f"/api/v1/services/{item_id}")
        assert not_found_response.status_code == 404


def test_services_admin_audit_fields_present():
    with TestClient(app) as client:
        login_as_admin(client)
        slug = f"service-audit-{uuid4().hex[:8]}"
        create_response = client.post(
            "/admin/services",
            data={
                "name": "Service Audit",
                "slug": slug,
                "summary": "summary",
                "description": "Deskripsi valid untuk audit fields service.",
                "status": "draft",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303

        items = client.get("/api/v1/services").json()["data"]
        created = next(item for item in items if item["slug"] == slug)
        assert created["created_by"] is not None
        assert created["updated_by"] is not None


def test_services_admin_filter_sort_search():
    with TestClient(app) as client:
        login_as_admin(client)
        unique_suffix = uuid4().hex[:6]
        draft_slug = f"service-filter-draft-{unique_suffix}"
        published_slug = f"service-filter-pub-{unique_suffix}"

        create_draft = client.post(
            "/admin/services",
            data={
                "name": f"Alpha Service {unique_suffix}",
                "slug": draft_slug,
                "summary": "summary draft",
                "description": "Deskripsi draft untuk validasi filter status service.",
                "status": "draft",
            },
            follow_redirects=False,
        )
        assert create_draft.status_code == 303

        create_published = client.post(
            "/admin/services",
            data={
                "name": f"Zulu Service {unique_suffix}",
                "slug": published_slug,
                "summary": "summary published",
                "description": "Deskripsi published untuk validasi search dan sort service.",
                "status": "published",
            },
            follow_redirects=False,
        )
        assert create_published.status_code == 303

        filtered = client.get(
            "/admin/services/partials/table",
            params={"q": unique_suffix, "status_filter": "published", "sort": "name_desc", "per_page": 20},
            headers={"HX-Request": "true"},
        )
        assert filtered.status_code == 200
        assert published_slug in filtered.text
        assert draft_slug not in filtered.text


def test_services_admin_duplicate_redirect():
    with TestClient(app) as client:
        login_as_admin(client)
        slug = f"services-duplicate-{uuid4().hex[:8]}"
        create_response = client.post(
            "/admin/services",
            data={
                "name": "Service Duplicate Source",
                "slug": slug,
                "summary": "sum",
                "description": "Deskripsi valid untuk duplicate service.",
                "status": "published",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303

        source = next(item for item in client.get("/api/v1/services").json()["data"] if item["slug"] == slug)
        duplicate_response = client.post(f"/admin/services/{source['id']}/duplicate", follow_redirects=False)
        assert duplicate_response.status_code == 303
        assert duplicate_response.headers["location"] == "/admin/services?result=duplicated"


def test_media_upload_requires_login():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("note.txt", b"hello", "text/plain")},
            follow_redirects=False,
        )
        assert response.status_code == 303
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "HTTP_ERROR"


def test_media_upload_rejects_invalid_extension():
    with TestClient(app) as client:
        login_as_admin(client)
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("malware.exe", b"abc", "text/plain")},
            follow_redirects=False,
        )
        assert response.status_code == 422
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "HTTP_ERROR"
        assert "not allowed" in payload["message"]


def test_media_upload_rejects_oversized_file():
    with TestClient(app) as client:
        login_as_admin(client)
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("large.txt", b"x" * 128, "text/plain")},
            follow_redirects=False,
        )
        assert response.status_code == 422
        payload = response.json()
        assert payload["success"] is False
        assert "exceeds max size" in payload["message"]


def test_media_upload_success():
    with TestClient(app) as client:
        login_as_admin(client)
        response = client.post(
            "/api/v1/media/upload",
            files={"file": ("ok.txt", b"tiny-content", "text/plain")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["original_name"] == "ok.txt"
        assert payload["data"]["size"] == len(b"tiny-content")


def test_media_list_after_upload():
    with TestClient(app) as client:
        login_as_admin(client)
        upload_response = client.post(
            "/api/v1/media/upload",
            files={"file": ("picker.txt", b"picker-content", "text/plain")},
        )
        assert upload_response.status_code == 200

        list_response = client.get("/api/v1/media/list", params={"limit": 20})
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["success"] is True
        assert any(item["name"].endswith("picker.txt") for item in payload["data"])


def test_server_draft_autosave_lifecycle():
    with TestClient(app) as client:
        login_as_admin(client)
        save_response = client.post(
            "/api/v1/drafts",
            json={
                "entity_type": "news",
                "entity_key": "create:new",
                "payload": {
                    "title": "Draft title",
                    "slug": "draft-title",
                    "content": "Draft content",
                    "status": "draft",
                },
            },
        )
        assert save_response.status_code == 200
        assert save_response.json()["success"] is True

        get_response = client.get("/api/v1/drafts", params={"entity_type": "news", "entity_key": "create:new"})
        assert get_response.status_code == 200
        data = get_response.json()["data"]
        assert data["payload"]["title"] == "Draft title"

        delete_response = client.delete("/api/v1/drafts", params={"entity_type": "news", "entity_key": "create:new"})
        assert delete_response.status_code == 200

        after_delete = client.get("/api/v1/drafts", params={"entity_type": "news", "entity_key": "create:new"})
        assert after_delete.status_code == 200
        assert after_delete.json()["data"] is None


def test_server_draft_recent_list_and_payload_limit():
    with TestClient(app) as client:
        login_as_admin(client)
        small_payload = {"title": "A", "slug": "a", "content": "x" * 20, "status": "draft"}
        save_response = client.post(
            "/api/v1/drafts",
            json={"entity_type": "news", "entity_key": "create:new", "payload": small_payload},
        )
        assert save_response.status_code == 200

        recent_response = client.get("/api/v1/drafts/recent", params={"limit": 5, "entity_type": "news"})
        assert recent_response.status_code == 200
        recent_data = recent_response.json()["data"]
        assert len(recent_data) >= 1
        assert recent_data[0]["entity_type"] == "news"

        very_large = {"content": "x" * 25000}
        too_large_response = client.post(
            "/api/v1/drafts",
            json={"entity_type": "news", "entity_key": "create:new", "payload": very_large},
        )
        assert too_large_response.status_code == 413


def test_admin_drafts_delete_flow():
    with TestClient(app) as client:
        login_as_admin(client)
        save_response = client.post(
            "/api/v1/drafts",
            json={
                "entity_type": "news",
                "entity_key": "create:new",
                "payload": {"title": "Draft delete test", "slug": "draft-delete-test"},
            },
        )
        assert save_response.status_code == 200

        delete_response = client.post(
            "/admin/drafts/delete",
            data={"entity_type": "news", "entity_key": "create:new"},
            follow_redirects=False,
        )
        assert delete_response.status_code == 303
        assert delete_response.headers["location"] == "/admin/drafts?result=deleted"

        check_response = client.get("/api/v1/drafts", params={"entity_type": "news", "entity_key": "create:new"})
        assert check_response.status_code == 200
        assert check_response.json()["data"] is None


def test_admin_drafts_bulk_delete_and_sort():
    with TestClient(app) as client:
        login_as_admin(client)
        first_save = client.post(
            "/api/v1/drafts",
            json={
                "entity_type": "news",
                "entity_key": "create:new",
                "payload": {"title": "First Draft", "slug": "first-draft"},
            },
        )
        assert first_save.status_code == 200

        second_save = client.post(
            "/api/v1/drafts",
            json={
                "entity_type": "news",
                "entity_key": "edit:99",
                "payload": {"title": "Second Draft", "slug": "second-draft"},
            },
        )
        assert second_save.status_code == 200

        newest_response = client.get("/admin/drafts", params={"sort": "newest"})
        oldest_response = client.get("/admin/drafts", params={"sort": "oldest"})
        assert newest_response.status_code == 200
        assert oldest_response.status_code == 200

        newest_html = newest_response.text
        oldest_html = oldest_response.text
        assert newest_html.find("Second Draft") < newest_html.find("First Draft")
        assert oldest_html.find("First Draft") < oldest_html.find("Second Draft")

        bulk_delete = client.post(
            "/admin/drafts/bulk-delete",
            data={"draft_refs": ["news::create:new", "news::edit:99"]},
            follow_redirects=False,
        )
        assert bulk_delete.status_code == 303
        assert bulk_delete.headers["location"] == "/admin/drafts?result=bulk-deleted"

        first_check = client.get("/api/v1/drafts", params={"entity_type": "news", "entity_key": "create:new"})
        second_check = client.get("/api/v1/drafts", params={"entity_type": "news", "entity_key": "edit:99"})
        assert first_check.status_code == 200
        assert second_check.status_code == 200
        assert first_check.json()["data"] is None
        assert second_check.json()["data"] is None


def test_canvas_api_save_and_load():
    with TestClient(app) as client:
        login_as_admin(client)
        payload = {
            "background": "#fafafa",
            "items": [
                {"id": "obj-1", "type": "rect", "x": 100, "y": 120, "w": 200, "h": 120, "stroke": "#000000", "fill": "#ffffff", "size": 2}
            ],
        }
        save_response = client.put(
            "/api/v1/canvas",
            json={"document_key": "default", "title": "Main Canvas", "payload": payload},
        )
        assert save_response.status_code == 200
        assert save_response.json()["success"] is True

        load_response = client.get("/api/v1/canvas", params={"document_key": "default"})
        assert load_response.status_code == 200
        data = load_response.json()["data"]
        assert data is not None
        assert data["document_key"] == "default"
        assert data["payload"]["background"] == "#fafafa"
        assert len(data["payload"]["items"]) == 1


def test_canvas_api_save_and_load_with_image_item():
    with TestClient(app) as client:
        login_as_admin(client)
        image_payload = {
            "background": "#ffffff",
            "items": [
                {
                    "id": "obj-image-1",
                    "type": "image",
                    "x": 10,
                    "y": 20,
                    "w": 512,
                    "h": 512,
                    "src": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2w==",
                }
            ],
        }
        save_response = client.put(
            "/api/v1/canvas",
            json={"document_key": "image-doc", "title": "Image Canvas", "payload": image_payload},
        )
        assert save_response.status_code == 200

        load_response = client.get("/api/v1/canvas", params={"document_key": "image-doc"})
        assert load_response.status_code == 200
        data = load_response.json()["data"]
        assert data is not None
        assert data["payload"]["items"][0]["type"] == "image"
        assert data["payload"]["items"][0]["w"] == 512
        assert data["payload"]["items"][0]["h"] == 512


def test_canvas_api_requires_login():
    with TestClient(app) as client:
        response = client.get("/api/v1/canvas", params={"document_key": "default"})
        assert response.status_code == 401


def test_canvas_api_payload_limit():
    with TestClient(app) as client:
        login_as_admin(client)
        large_payload = {"items": [{"id": f"obj-{i}", "type": "text", "text": "x" * 200} for i in range(800)]}
        response = client.put(
            "/api/v1/canvas",
            json={"document_key": "default", "title": "Main Canvas", "payload": large_payload},
        )
        assert response.status_code == 413


def test_canvas_api_conflict_guard():
    with TestClient(app) as client:
        login_as_admin(client)
        initial_payload = {"background": "#fff", "items": [{"id": "obj-1", "type": "text", "text": "v1"}]}
        first_save = client.put(
            "/api/v1/canvas",
            json={"document_key": "conflict-doc", "title": "Conflict Doc", "payload": initial_payload},
        )
        assert first_save.status_code == 200
        stale_version = first_save.json()["data"]["updated_at"]

        second_payload = {"background": "#fff", "items": [{"id": "obj-1", "type": "text", "text": "v2"}]}
        second_save = client.put(
            "/api/v1/canvas",
            json={"document_key": "conflict-doc", "title": "Conflict Doc", "payload": second_payload},
        )
        assert second_save.status_code == 200

        stale_attempt_payload = {"background": "#fff", "items": [{"id": "obj-1", "type": "text", "text": "stale"}]}
        stale_attempt = client.put(
            "/api/v1/canvas",
            json={
                "document_key": "conflict-doc",
                "title": "Conflict Doc",
                "payload": stale_attempt_payload,
                "last_known_updated_at": stale_version,
            },
        )
        assert stale_attempt.status_code == 409

        force_attempt = client.put(
            "/api/v1/canvas",
            json={
                "document_key": "conflict-doc",
                "title": "Conflict Doc",
                "payload": stale_attempt_payload,
                "last_known_updated_at": stale_version,
                "force": True,
            },
        )
        assert force_attempt.status_code == 200


def test_canvas_api_documents_list():
    with TestClient(app) as client:
        login_as_admin(client)
        first = client.put(
            "/api/v1/canvas",
            json={"document_key": "landing", "title": "Landing", "payload": {"background": "#fff", "items": []}},
        )
        second = client.put(
            "/api/v1/canvas",
            json={"document_key": "promo", "title": "Promo", "payload": {"background": "#eee", "items": []}},
        )
        assert first.status_code == 200
        assert second.status_code == 200

        response = client.get("/api/v1/canvas/documents", params={"limit": 10})
        assert response.status_code == 200
        data = response.json()["data"]
        keys = [item["document_key"] for item in data]
        assert "landing" in keys
        assert "promo" in keys


def test_canvas_api_rename_and_delete_document():
    with TestClient(app) as client:
        login_as_admin(client)
        create_response = client.put(
            "/api/v1/canvas",
            json={"document_key": "wireframe", "title": "Wireframe", "payload": {"background": "#fff", "items": []}},
        )
        assert create_response.status_code == 200

        rename_response = client.patch(
            "/api/v1/canvas",
            json={"document_key": "wireframe", "new_document_key": "wireframe-v2", "title": "Wireframe v2"},
        )
        assert rename_response.status_code == 200
        assert rename_response.json()["data"]["document_key"] == "wireframe-v2"

        check_response = client.get("/api/v1/canvas", params={"document_key": "wireframe-v2"})
        assert check_response.status_code == 200
        assert check_response.json()["data"]["title"] == "Wireframe v2"

        delete_response = client.delete("/api/v1/canvas", params={"document_key": "wireframe-v2"})
        assert delete_response.status_code == 200

        after_delete = client.get("/api/v1/canvas", params={"document_key": "wireframe-v2"})
        assert after_delete.status_code == 200
        assert after_delete.json()["data"] is None


def test_canvas_permissions_for_editor_user():
    with TestClient(app) as client:
        login_as_editor(client)
        read_response = client.get("/api/v1/canvas/documents", params={"limit": 5})
        assert read_response.status_code == 200

        save_response = client.put(
            "/api/v1/canvas",
            json={"document_key": "editor-attempt", "title": "Editor Attempt", "payload": {"background": "#fff", "items": []}},
        )
        assert save_response.status_code == 403
