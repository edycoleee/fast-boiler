from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.news.repository import NewsRepository
from app.modules.news.service import NewsService
from app.modules.services.repository import ServicesRepository
from app.modules.services.service import ServicesService

router = APIRouter(tags=["home-public"])


def get_news_service(db: Session = Depends(get_db)) -> NewsService:
    return NewsService(NewsRepository(db))


def get_services_service(db: Session = Depends(get_db)) -> ServicesService:
    return ServicesService(ServicesRepository(db))


@router.get("/")
def home_landing(
    request: Request,
    news_service: NewsService = Depends(get_news_service),
    services_service: ServicesService = Depends(get_services_service),
):
    news_items, _, _, _ = news_service.list_news(page=1, per_page=3)
    service_items, _, _, _ = services_service.list_services(page=1, per_page=3)
    hero = {
        "eyebrow": "Fast Boiler",
        "title": "Modern Corporate Landing Template",
        "description": (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec feugiat, mauris vitae commodo egestas, "
            "magna erat hendrerit dui, non blandit arcu velit eu lorem. Proin faucibus nisl a tortor cursus, vitae "
            "congue purus volutpat."
        ),
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
        },
    )
