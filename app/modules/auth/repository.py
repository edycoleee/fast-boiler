from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.auth.models import Permission, Role, User


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(
            select(User).options(selectinload(User.role).selectinload(Role.permissions)).where(User.username == username)
        )

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.scalar(
            select(User).options(selectinload(User.role).selectinload(Role.permissions)).where(User.id == user_id)
        )

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))

    def get_permission_by_code(self, code: str) -> Permission | None:
        return self.db.scalar(select(Permission).where(Permission.code == code))

    def create_role(self, name: str) -> Role:
        role = Role(name=name)
        self.db.add(role)
        self.db.flush()
        return role

    def create_permission(self, code: str) -> Permission:
        permission = Permission(code=code)
        self.db.add(permission)
        self.db.flush()
        return permission

    def add_permission_to_role(self, role: Role, permission: Permission) -> None:
        if permission not in role.permissions:
            role.permissions.append(permission)
            self.db.add(role)
            self.db.flush()

    def create_user(self, username: str, password_hash: str, role_name: str = "editor") -> User:
        role = self.get_role_by_name(role_name)
        if role is None:
            role = self.create_role(role_name)
        user = User(username=username, password_hash=password_hash, role_id=role.id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def commit(self) -> None:
        self.db.commit()
