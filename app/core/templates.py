from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.config import settings

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.globals["theme_tokens"] = {
    "page": settings.theme_color_page,
    "surface": settings.theme_color_surface,
    "text": settings.theme_color_text,
    "muted": settings.theme_color_muted,
    "border": settings.theme_color_border,
    "brand": settings.theme_color_brand,
    "brand_foreground": settings.theme_color_brand_foreground,
}
