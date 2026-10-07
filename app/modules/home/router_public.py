from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService
from app.modules.settings.repository import SettingsRepository
from app.modules.settings.service import SettingsService
from app.modules.services.repository import ServicesRepository
from app.modules.services.service import ServicesService

router = APIRouter(tags=["home-public"])


def get_news_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(NewsRepository(db))


def get_services_service(db: Session = Depends(get_db)) -> ServicesService:
    return ServicesService(ServicesRepository(db))


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(SettingsRepository(db))


@router.get("/")
def home_landing(
    request: Request,
    news_service: NewsService = Depends(get_news_service),
    services_service: ServicesService = Depends(get_services_service),
    settings_service: SettingsService = Depends(get_settings_service),
):
    news_items, _, _, _ = news_service.list_news(page=1, per_page=3)
    service_items, _, _, _ = services_service.list_services(page=1, per_page=3)
    site_settings = settings_service.get_site_settings()
    hero = {
        "eyebrow": site_settings["site_name"],
        "title": site_settings["site_name"],
        "description": site_settings["site_tagline"],
    }
    stats = [
        {"label": "Client Satisfaction", "value": "98%", "description": "Lorem ipsum dolor sit amet, consectetur."},
        {"label": "Successful Projects", "value": "240+", "description": "Donec feugiat mauris vitae commodo egestas."},
        {"label": "Team Members", "value": "35", "description": "Mauris blandit arcu velit eu lorem."},
        {"label": "Support Availability", "value": "24/7", "description": "Proin faucibus nisl a tortor cursus."},
    ]
    testimonials = [
        {
            "name": "Aldo Pratama",
            "role": "Operations Manager",
            "quote": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc efficitur urna sed magna tempor.",
        },
        {
            "name": "Nadia Lestari",
            "role": "Head of Digital Transformation",
            "quote": "Donec feugiat mauris vitae commodo egestas. Quisque rutrum sapien sed velit suscipit.",
        },
        {
            "name": "Rafi Kurniawan",
            "role": "Program Director",
            "quote": "Proin faucibus nisl a tortor cursus, vitae congue purus volutpat. Integer quis lacus et neque.",
        },
    ]
    return templates.TemplateResponse(
        request=request,
        name="public/home.html",
        context={
            "hero": hero,
            "stats": stats,
            "testimonials": testimonials,
            "news_items": news_items,
            "service_items": service_items,
            "site_settings": site_settings,
        },
    )
