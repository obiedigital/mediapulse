from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .article import Article


class StoryCluster(Base, TimestampMixin):
    """A dedup group: the same underlying story picked up by N outlets.

    pickup_count is the reach signal used in the Daily Brief and SOV charts.
    cluster_key is a normalised-title fingerprint (see ingestion/dedupe.py)
    used for fast fuzzy-match lookups before falling back to a full scan.
    """

    __tablename__ = "story_clusters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)

    cluster_key: Mapped[str] = mapped_column(String(64), index=True)
    primary_article_id: Mapped[str | None] = mapped_column(String, nullable=True)
    pickup_count: Mapped[int] = mapped_column(Integer, default=1)

    first_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    articles: Mapped[list["Article"]] = relationship(back_populates="story_cluster")

    def __repr__(self) -> str:
        return f"StoryCluster(cluster_key={self.cluster_key!r}, pickups={self.pickup_count})"
