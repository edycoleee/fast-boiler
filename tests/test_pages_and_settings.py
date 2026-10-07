from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def login_as_admin(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_pages_public_only_shows_published():
    with TestClient(app) as client:
        slug_published = f"page-published-{uuid4().hex[:8]}"
        slug_draft = f"page-draft-{uuid4().hex[:8]}"

        response_published = client.post(
            "/api/v1/pages",
            json={
                "title": "Published Page",
                "slug": slug_published,
                "summary": "Summary published",
                "content": "Konten halaman published yang valid untuk ditampilkan.",
                "status": "published",
            },
        )
        assert response_published.status_code == 201

        response_draft = client.post(
            "/api/v1/pages",
            json={
                "title": "Draft Page",
                "slug": slug_draft,
                "summary": "Summary draft",
                "content": "Konten halaman draft yang valid namun tidak tampil di publik.",
                "status": "draft",
            },
        )
        assert response_draft.status_code == 201

        listing = client.get("/pages")
        assert listing.status_code == 200
        assert slug_published in listing.text
        assert slug_draft not in listing.text

        detail_published = client.get(f"/pages/{slug_published}")
        assert detail_published.status_code == 200

        detail_draft = client.get(f"/pages/{slug_draft}")
        assert detail_draft.status_code == 404


def test_pages_api_crud_cycle():
    with TestClient(app) as client:
        slug = f"page-api-cycle-{uuid4().hex[:8]}"
        create_response = client.post(
            "/api/v1/pages",
            json={
                "title": "Page API Cycle",
                "slug": slug,
                "summary": "Summary API cycle",
                "content": "Konten API cycle untuk validasi create update delete pada page.",
                "status": "draft",
            },
        )
        assert create_response.status_code == 201
        page_id = create_response.json()["data"]["id"]

        get_response = client.get(f"/api/v1/pages/{page_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["slug"] == slug

        update_response = client.put(
            f"/api/v1/pages/{page_id}",
            json={"title": "Page API Cycle Updated", "status": "published"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["status"] == "published"

        delete_response = client.delete(f"/api/v1/pages/{page_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        missing = client.get(f"/api/v1/pages/{page_id}")
        assert missing.status_code == 404


def test_pages_admin_prg_cycle():
    with TestClient(app) as client:
        login_as_admin(client)
        slug = f"page-admin-{uuid4().hex[:8]}"

        create_response = client.post(
            "/admin/pages",
            data={
                "title": "Page Admin Create",
                "slug": slug,
                "summary": "Summary admin",
                "content": "Konten admin untuk create page yang valid.",
                "status": "draft",
            },
            follow_redirects=False,
        )
        assert create_response.status_code == 303
        assert create_response.headers["location"] == "/admin/pages?result=created"

        listed = client.get("/api/v1/pages").json()["data"]
        created = next(item for item in listed if item["slug"] == slug)
        page_id = created["id"]

        update_response = client.post(
            f"/admin/pages/{page_id}",
            data={
                "title": "Page Admin Updated",
                "slug": slug,
                "summary": "Summary updated",
                "content": "Konten admin untuk update page yang valid.",
                "status": "published",
            },
            follow_redirects=False,
        )
        assert update_response.status_code == 303
        assert update_response.headers["location"] == "/admin/pages?result=updated"

        delete_response = client.post(f"/admin/pages/{page_id}/delete", follow_redirects=False)
        assert delete_response.status_code == 303
        assert delete_response.headers["location"] == "/admin/pages?result=deleted"


def test_pages_admin_filter_sort_search():
    with TestClient(app) as client:
        login_as_admin(client)
        unique_suffix = uuid4().hex[:6]
        draft_slug = f"page-filter-draft-{unique_suffix}"
        published_slug = f"page-filter-pub-{unique_suffix}"

        create_draft = client.post(
            "/admin/pages",
            data={
                "title": f"Alpha Page {unique_suffix}",
                "slug": draft_slug,
                "summary": "summary draft",
                "content": "Konten draft valid untuk pengujian filter page admin.",
                "status": "draft",
            },
            follow_redirects=False,
        )
        assert create_draft.status_code == 303

        create_published = client.post(
            "/admin/pages",
            data={
                "title": f"Zulu Page {unique_suffix}",
                "slug": published_slug,
                "summary": "summary published",
                "content": "Konten published valid untuk pengujian sort page admin.",
                "status": "published",
            },
            follow_redirects=False,
        )
        assert create_published.status_code == 303

        filtered = client.get(
            "/admin/pages",
            params={"q": unique_suffix, "status_filter": "published", "sort": "title_desc", "per_page": 20},
        )
        assert filtered.status_code == 200
        assert published_slug in filtered.text
        assert draft_slug not in filtered.text


def test_settings_update_reflects_on_homepage():
    with TestClient(app) as client:
        login_as_admin(client)
        unique_suffix = uuid4().hex[:6]
        updated_name = f"Fast Boiler {unique_suffix}"
        updated_tagline = f"Tagline {unique_suffix} for modern web baseline"
        updated_email = f"contact-{unique_suffix}@example.com"

        update_response = client.post(
            "/admin/settings",
            data={
                "site_name": updated_name,
                "site_tagline": updated_tagline,
                "contact_email": updated_email,
            },
            follow_redirects=False,
        )
        assert update_response.status_code == 303
        assert update_response.headers["location"] == "/admin/settings?result=updated"

        home_response = client.get("/")
        assert home_response.status_code == 200
        assert updated_name in home_response.text
        assert updated_tagline in home_response.text

        api_response = client.get("/api/v1/settings/site")
        assert api_response.status_code == 200
        body = api_response.json()
        assert body["site_name"] == updated_name
        assert body["site_tagline"] == updated_tagline
        assert body["contact_email"] == updated_email
