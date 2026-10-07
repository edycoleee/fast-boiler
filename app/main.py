from __future__ import annotations

from datetime import datetime, timezone
from contextlib import asynccontextmanager
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler as fastapi_http_exception_handler
from fastapi.exception_handlers import request_validation_exception_handler as fastapi_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.core.logging_config import configure_logging
from app.core.security import hash_password
from app.modules.design_system.router_public import router as design_system_public_router
from app.modules.drafts.router_api import router as drafts_api_router
from app.modules.drafts.router_admin import router as drafts_admin_router
from app.modules.drafts.repository import DraftRepository
from app.modules.home.router_public import router as home_public_router
from app.modules.pages.router_public import router as pages_public_router
from app.modules.pages.router_api import router as pages_api_router
from app.modules.pages.router_admin import router as pages_admin_router
from app.modules.dashboard.router_admin import router as dashboard_admin_router
from app.modules.canvas.router_admin import router as canvas_admin_router
from app.modules.canvas.router_api import router as canvas_api_router
from app.modules.media.router_api import router as media_api_router
from app.modules.media.router_admin import router as media_admin_router
from app.modules.logger.router_admin import router as logger_admin_router
from app.modules.settings.router_admin import router as settings_admin_router
from app.modules.settings.router_api import router as settings_api_router
from app.modules.auth.repository import AuthRepository
from app.modules.auth.router import router as auth_router
from app.modules.auth.service import AuthService
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.news.router_admin import router as news_admin_router
from app.modules.news.router_api import router as news_api_router
from app.modules.news.router_htmx import router as news_htmx_router
from app.modules.news.router_public import router as news_public_router
from app.modules.news.schemas import ApiError, ApiMeta, ApiResponse
from app.modules.news import models as news_models  # noqa: F401
from app.modules.services import models as services_models  # noqa: F401
from app.modules.pages import models as pages_models  # noqa: F401
from app.modules.settings import models as settings_models  # noqa: F401
from app.modules.logger import models as logger_models  # noqa: F401
from app.modules.services.router_admin import router as services_admin_router
from app.modules.services.router_api import router as services_api_router
from app.modules.services.router_htmx import router as services_htmx_router
from app.modules.services.router_public import router as services_public_router
from app.modules.drafts import models as drafts_models  # noqa: F401
from app.modules.canvas import models as canvas_models  # noqa: F401
from app.modules.logger.repository import LoggerRepository
from app.modules.logger.service import LoggerService


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env in {"development", "test"}:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        required_schema = {
            "users": {"role_id"},
            "news": {"created_by", "updated_by"},
            "services": {"created_by", "updated_by"},
        }
        for table_name, required_columns in required_schema.items():
            if table_name not in table_names:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            if not required_columns.issubset(existing_columns):
                Base.metadata.drop_all(bind=engine)
                break
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        repo = AuthRepository(db)
        auth_service = AuthService(repo)
        auth_service.ensure_default_rbac()
        if repo.get_by_username("admin") is None:
            repo.create_user(username="admin", password_hash=hash_password("admin123"), role_name="admin")
    finally:
        db.close()
    yield


configure_logging()
logger = logging.getLogger("app.main")

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age,
    same_site=settings.session_same_site,
    https_only=settings.session_https_only,
)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id", str(uuid4()))
    return await call_next(request)


@app.middleware("http")
async def log_request_response(request: Request, call_next):
    started = time.perf_counter()
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "n/a")
    request.state.request_id = request_id
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    message = f'{request.method} {request.url.path} -> {response.status_code} in {duration_ms:.2f}ms req_id={request_id}'
    if response.status_code >= 500:
        level = "ERROR"
        logger.error(message)
    elif response.status_code >= 400:
        level = "WARNING"
        logger.warning(message)
    else:
        level = "INFO"
        logger.info(message)
    db = SessionLocal()
    try:
        LoggerService(LoggerRepository(db)).write_request_log(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            level=level,
            duration_ms=duration_ms,
            message=message[:500],
        )
    except Exception:
        logger.exception("Failed to persist request log req_id=%s path=%s", request_id, request.url.path)
    finally:
        db.close()
    return response


@app.middleware("http")
async def attach_admin_draft_count(request: Request, call_next):
    request.state.draft_count = 0
    session_data = request.scope.get("session") or {}
    user_id = session_data.get("user_id")
    if user_id and request.url.path.startswith("/admin"):
        db = SessionLocal()
        try:
            repo = DraftRepository(db)
            request.state.draft_count = repo.count_for_user(int(user_id))
        finally:
            db.close()
    return await call_next(request)


def _api_error_response(request: Request, http_status: int, message: str, code: str, details: list[dict[str, str]] | None = None):
    payload = ApiResponse[None](
        success=False,
        message=message,
        error=ApiError(code=code, details=details),
        meta=ApiMeta(
            request_id=getattr(request.state, "request_id", str(uuid4())),
            timestamp=datetime.now(timezone.utc),
        ),
    )
    return JSONResponse(status_code=http_status, content=payload.model_dump(mode="json"))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTPException status=%s path=%s detail=%s req_id=%s",
        exc.status_code,
        request.url.path,
        exc.detail,
        getattr(request.state, "request_id", "n/a"),
    )
    if request.url.path.startswith("/api/v1/"):
        detail_text = str(exc.detail)
        code = {
            status.HTTP_404_NOT_FOUND: "NOT_FOUND",
            status.HTTP_409_CONFLICT: "CONFLICT",
            status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
            status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        }.get(exc.status_code, "HTTP_ERROR")
        return _api_error_response(request, exc.status_code, detail_text, code)
    return await fastapi_http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "ValidationError path=%s errors=%s req_id=%s",
        request.url.path,
        exc.errors(),
        getattr(request.state, "request_id", "n/a"),
    )
    if request.url.path.startswith("/api/v1/"):
        details = [{"field": ".".join(str(x) for x in err["loc"]), "reason": err["msg"]} for err in exc.errors()]
        return _api_error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Validation failed",
            "VALIDATION_ERROR",
            details,
        )
    return await fastapi_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception path=%s req_id=%s",
        request.url.path,
        getattr(request.state, "request_id", "n/a"),
    )
    if request.url.path.startswith("/api/v1/"):
        return _api_error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error",
            "INTERNAL_SERVER_ERROR",
            [{"error": str(exc)}],
        )
    raise exc


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


app.include_router(home_public_router)
app.include_router(design_system_public_router)
app.include_router(news_public_router)
app.include_router(services_public_router)
app.include_router(pages_public_router)
app.include_router(auth_router)
app.include_router(dashboard_admin_router)
app.include_router(news_admin_router)
app.include_router(news_htmx_router)
app.include_router(news_api_router)
app.include_router(drafts_api_router)
app.include_router(drafts_admin_router)
app.include_router(media_api_router)
app.include_router(media_admin_router)
app.include_router(logger_admin_router)
app.include_router(settings_api_router)
app.include_router(settings_admin_router)
app.include_router(canvas_admin_router)
app.include_router(canvas_api_router)
app.include_router(services_admin_router)
app.include_router(services_htmx_router)
app.include_router(services_api_router)
app.include_router(pages_admin_router)
app.include_router(pages_api_router)
