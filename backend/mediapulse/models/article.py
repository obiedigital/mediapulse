from __future__ import annotations

import enum
import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .classification import Classification
    from .story_cluster import StoryCluster
    from .topic import Topic


class ArticleStatus(str, enum.Enum):
    new = "new"  # ingested, not yet classified
    processing = "processing"  # classification in flight
    classified = "classified"  # AI enrichment complete
    needs_review = "needs_review"  # low-confidence date/segmentation, human check
    rejected = "rejected"  # advert/notice/non-editorial, excluded from coverage counts
    error = "error"  # classification failed after retries; sits in reprocessing queue


class Article(Base, TimestampMixin):
    """One editorial item (a web story, or one segmented article from a
    print PDF page). This is the unit AI enrichment and dedupe operate on.

    tenant_id is denormalized from topic.tenant_id — every article query is
    tenant-scoped, so paying one JOIN's worth of write-time redundancy back
    at every read is the right trade.
    """

    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), index=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    story_cluster_id: Mapped[str | None] = mapped_column(
        ForeignKey("story_clusters.id"), nullable=True, index=True
    )

    publication: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(1024))
    byline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    section: Mapped[str | None] = mapped_column(String(128), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_advert: Mapped[bool] = mapped_column(Boolean, default=False)

    # published_at is the *true* publication date (parsed from masthead for
    # print, or feed metadata for web) — never the ingestion date. Bug #2
    # in the legacy pipeline conflated these; see ingestion/dates.py.
    published_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at_confidence: Mapped[str] = mapped_column(String(16), default="unknown")
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ArticleStatus] = mapped_column(Enum(ArticleStatus), default=ArticleStatus.new)

    topic: Mapped["Topic"] = relationship()
    story_cluster: Mapped["StoryCluster | None"] = relationship(back_populates="articles")
    classification: Mapped["Classification | None"] = relationship(
        back_populates="article", uselist=False
    )

    def __repr__(self) -> str:
        return f"Article(title={self.title[:40]!r}, status={self.status!r})"
