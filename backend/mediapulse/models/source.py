from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .topic import Topic


class SourceType(str, enum.Enum):
    rss = "rss"
    pressreader = "pressreader"
    pdf_upload = "pdf_upload"
    manual_link = "manual_link"
    # future connectors — architecture allows adding without a schema change
    social = "social"
    broadcast_transcript = "broadcast_transcript"
    google_alerts = "google_alerts"


class Source(Base, TimestampMixin):
    """A feed/outlet MediaPulse ingests from, scoped to one topic.

    Source-health (last fetch, error streak) lives directly on the row so
    the admin source-health page is a single-table read.
    """

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), index=True)

    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)

    last_fetched_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    topic: Mapped["Topic"] = relationship()

    def __repr__(self) -> str:
        return f"Source(name={self.name!r}, type={self.type!r})"
