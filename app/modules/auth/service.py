from __future__ import annotations

from fastapi import HTTPException, status

from app.core.security import verify_password
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def authenticate(self, username: str, password: str) -> User:
        user = self.repository.get_by_username(username=username)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        return user

    def get_user(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)

    def ensure_default_rbac(self) -> None:
        admin_role = self.repository.get_role_by_name("admin") or self.repository.create_role("admin")
        editor_role = self.repository.get_role_by_name("editor") or self.repository.create_role("editor")

        all_permissions = [
            "news.manage",
            "services.manage",
            "media.manage",
            "canvas.manage",
            "news.read",
            "services.read",
            "canvas.read",
        ]
        for code in all_permissions:
            permission = self.repository.get_permission_by_code(code) or self.repository.create_permission(code)
            if code.endswith(".manage"):
                self.repository.add_permission_to_role(admin_role, permission)
            else:
                self.repository.add_permission_to_role(admin_role, permission)
                self.repository.add_permission_to_role(editor_role, permission)
        self.repository.commit()

    def user_has_permission(self, user: User, permission_code: str) -> bool:
        return any(permission.code == permission_code for permission in user.role.permissions)
