from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(".env"))


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Fast Boiler")
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    db_url: str = os.getenv("DB_URL", "sqlite:///data/app.db")
    theme_color_page: str = os.getenv("THEME_COLOR_PAGE", "248 250 252")
    theme_color_surface: str = os.getenv("THEME_COLOR_SURFACE", "255 255 255")
    theme_color_text: str = os.getenv("THEME_COLOR_TEXT", "15 23 42")
    theme_color_muted: str = os.getenv("THEME_COLOR_MUTED", "100 116 139")
    theme_color_border: str = os.getenv("THEME_COLOR_BORDER", "226 232 240")
    theme_color_brand: str = os.getenv("THEME_COLOR_BRAND", "37 99 235")
    theme_color_brand_foreground: str = os.getenv("THEME_COLOR_BRAND_FOREGROUND", "255 255 255")
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "fast_boiler_session")
    session_max_age: int = _env_int("SESSION_MAX_AGE", 86400)
    session_same_site: str = os.getenv("SESSION_SAME_SITE", "lax")
    session_https_only: bool = _env_bool("SESSION_HTTPS_ONLY", False)
    media_dir: str = os.getenv("MEDIA_DIR", "media/uploads")
    media_max_size_bytes: int = _env_int("MEDIA_MAX_SIZE_BYTES", 2 * 1024 * 1024)
    media_allowed_extensions: str = os.getenv("MEDIA_ALLOWED_EXTENSIONS", "jpg,jpeg,png,webp,pdf,txt")
    media_allowed_mime_types: str = os.getenv(
        "MEDIA_ALLOWED_MIME_TYPES",
        "image/jpeg,image/png,image/webp,application/pdf,text/plain",
    )
    draft_retention_days: int = _env_int("DRAFT_RETENTION_DAYS", 30)
    draft_max_payload_chars: int = _env_int("DRAFT_MAX_PAYLOAD_CHARS", 20000)
    draft_min_save_interval_seconds: int = _env_int("DRAFT_MIN_SAVE_INTERVAL_SECONDS", 2)
    canvas_max_payload_chars: int = _env_int("CANVAS_MAX_PAYLOAD_CHARS", 120000)


settings = Settings()
