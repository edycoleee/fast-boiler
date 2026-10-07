from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.templates import templates
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginForm
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": None})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    service: AuthService = Depends(get_service),
):
    try:
        form = LoginForm(username=username, password=password)
        user = service.authenticate(form.username, form.password)
    except (HTTPException, ValidationError):
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={"error": "Username atau password tidak valid."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.session["user_id"] = user.id
    request.session["role"] = user.role.name
    request.session["username"] = user.username
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
