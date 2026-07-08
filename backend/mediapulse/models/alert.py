from __future__ import annotations

import datetime as dt
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .article import Article


class AlertType(str, enum.Enum):
    negative_sentiment = "negative_sentiment"  # a negative story about the tenant's own brand
    competitor_launch = "competitor_launch"  # a competitor product/service launch
    regulator_announcement = "regulator_announcement"  # any new regulator-pillar story
    volume_spike = "volume_spike"  # today's coverage volume well above trailing baseline


class Alert(Base, TimestampMixin):
    """A near-real-time notification candidate. Created as a side effect of
    classification (`alerts/rules.py`) so an alert-worthy story is flagged
    the moment it's enriched, not on some later batch schedule. `article_id`
    is null for `volume_spike`, which is a per-day signal rather than
    being about one story.

    Idempotency: article-scoped alert types are unique per
    (article_id, alert_type) — reclassifying an article (e.g. via
    --reprocess-errors) must not re-notify on the same story twice.
    """

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    article_id: Mapped[str | None] = mapped_column(ForeignKey("articles.id"), nullable=True, index=True)

    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType))
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    article: Mapped["Article | None"] = relationship()

    def __repr__(self) -> str:
        return f"Alert(type={self.alert_type!r}, article_id={self.article_id!r})"
