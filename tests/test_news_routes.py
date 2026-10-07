from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


def test_healthcheck():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_root_landing_page():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Fast Boiler" in response.text


def test_news_api_list_shape():
    with TestClient(app) as client:
        response = client.get("/api/v1/news")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "meta" in body
        assert "data" in body


def test_design_system_page():
    with TestClient(app) as client:
        response = client.get("/design-system")
        assert response.status_code == 200
        assert "UI Components and Theme Tokens" in response.text
        assert "Navigation Components" in response.text
        assert "Advanced Table Utilities" in response.text


def test_news_detail_not_found_page():
    with TestClient(app) as client:
        response = client.get("/news/slug-yang-tidak-ada")
        assert response.status_code == 404


def test_news_api_not_found_error_shape():
    with TestClient(app) as client:
        response = client.get("/api/v1/news/999999")
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"
        assert "meta" in body


def test_news_detail_page_success():
    with TestClient(app) as client:
        slug = "news-public-detail-success"
        create_response = client.post(
            "/api/v1/news",
            json={
                "title": "Public Detail Success",
                "slug": slug,
                "excerpt": "Excerpt",
                "content": "Konten detail sukses untuk validasi route publik.",
                "status": "published",
            },
        )
        assert create_response.status_code == 201

        detail_response = client.get(f"/news/{slug}")
        assert detail_response.status_code == 200
        assert "Public Detail Success" in detail_response.text


def test_news_api_crud_cycle():
    with TestClient(app) as client:
        slug = f"news-api-cycle-{uuid4().hex[:8]}"
        create_response = client.post(
            "/api/v1/news",
            json={
                "title": "News API Cycle",
                "slug": slug,
                "excerpt": "Cycle excerpt",
                "content": "Konten API cycle untuk validasi create update delete.",
                "status": "draft",
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()["data"]
        news_id = created["id"]

        get_response = client.get(f"/api/v1/news/{news_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["slug"] == slug

        update_response = client.put(
            f"/api/v1/news/{news_id}",
            json={
                "title": "News API Cycle Updated",
                "status": "published",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["title"] == "News API Cycle Updated"

        delete_response = client.delete(f"/api/v1/news/{news_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        not_found_response = client.get(f"/api/v1/news/{news_id}")
        assert not_found_response.status_code == 404
