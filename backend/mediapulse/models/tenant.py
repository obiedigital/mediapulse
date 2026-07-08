from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .topic import Topic
    from .user import User


class Tenant(Base, TimestampMixin):
    """A client organisation (Orange Botswana, a bank, a mining house, ...).

    `brand_config` carries theme (colors/logo) for the client portal.
    `watchlist_config` is a starting point for topic/keyword seeding when a
    tenant is onboarded; the durable, editable watchlist lives in `Topic`.
    """

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    brand_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    watchlist_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Scheduler delivery targets: {"brief_recipients": [...], "alert_recipients": [...],
    # "daily_brief_hour_utc": 6}. Empty/absent means "generate but don't email" —
    # the scheduler treats a tenant with no recipients as opted out of automated
    # delivery, not an error.
    notification_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    topics: Mapped[list["Topic"]] = relationship(back_populates="tenant")

    def __repr__(self) -> str:
        return f"Tenant(slug={self.slug!r})"
