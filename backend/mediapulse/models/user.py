from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .tenant import Tenant


class UserRole(str, enum.Enum):
    platform_admin = "platform_admin"  # DS Communications staff, cross-tenant
    admin = "admin"  # agency coordinator, tenant-scoped
    analyst = "analyst"  # media lead / strategist, tenant-scoped
    client_viewer = "client_viewer"  # client CMO, read-only, tenant-scoped


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    # Null tenant_id is reserved for platform_admin users who operate across tenants.
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("tenants.id"), index=True, nullable=True
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.analyst)
    is_active: Mapped[bool] = mapped_column(default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    def __repr__(self) -> str:
        return f"User(email={self.email!r}, role={self.role!r})"
