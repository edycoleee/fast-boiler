from __future__ import annotations

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.news.repository import NewsRepository
from app.modules.news.schemas import NewsCreate
from app.modules.services.repository import ServicesRepository
from app.modules.services.schemas import ServiceCreate


def run_seed() -> None:
    db = SessionLocal()
    try:
        auth_repo = AuthRepository(db)
        auth_service = AuthService(auth_repo)
        auth_service.ensure_default_rbac()

        admin = auth_repo.get_by_username("admin")
        if admin is None:
            auth_repo.create_user("admin", hash_password("admin123"), role_name="admin")

        news_repo = NewsRepository(db)
        if news_repo.get_by_slug("welcome-fast-boiler") is None:
            news_repo.create(
                NewsCreate(
                    title="Welcome to Fast Boiler",
                    slug="welcome-fast-boiler",
                    excerpt="Starter seeded article.",
                    content="This is a seeded article for bootstrapping development.",
                    status="published",
                )
            )

        services_repo = ServicesRepository(db)
        if services_repo.get_by_slug("general-consultation") is None:
            services_repo.create(
                ServiceCreate(
                    name="General Consultation",
                    slug="general-consultation",
                    summary="Starter seeded service.",
                    description="This is a seeded service for bootstrapping development.",
                    status="published",
                )
            )
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
