from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


def require_admin_session(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    session_user_id = request.session.get("user_id")
    session_role = request.session.get("role")

    if session_user_id is None or session_role is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Login required",
            headers={"Location": "/auth/login"},
        )

    user = service.get_user(int(session_user_id))
    if user is None or user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_permission(permission_code: str):
    def _require_permission(
        request: Request,
        service: AuthService = Depends(get_auth_service),
    ):
        session_user_id = request.session.get("user_id")
        if session_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail="Login required",
                headers={"Location": "/auth/login"},
            )
        user = service.get_user(int(session_user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail="Login required",
                headers={"Location": "/auth/login"},
            )
        if not service.user_has_permission(user, permission_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return user

    return _require_permission
