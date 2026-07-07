from __future__ import annotations

import datetime as dt
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .tenant import Tenant


class BriefType(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class BriefStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    sent = "sent"


class Brief(Base, TimestampMixin):
    """A generated brief (daily/weekly/monthly) — the flagship deliverable.

    html_content is the rendered, email-safe brief body; pdf_path points at
    the WeasyPrint-rendered export. Kept as an archive row per tenant per
    period so the React 'Daily Brief archive' view is a simple list query.
    """

    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)

    brief_type: Mapped[BriefType] = mapped_column(Enum(BriefType))
    status: Mapped[BriefStatus] = mapped_column(Enum(BriefStatus), default=BriefStatus.draft)

    period_start: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    model_used: Mapped[str | None] = mapped_column(String(128), nullable=True)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    generated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship()

    def __repr__(self) -> str:
        return f"Brief(tenant_id={self.tenant_id!r}, type={self.brief_type!r}, period_end={self.period_end!r})"
