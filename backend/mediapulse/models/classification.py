from __future__ import annotations

import datetime as dt
import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from .article import Article


class SentimentLabel(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class ThreatTag(str, enum.Enum):
    opportunity = "opportunity"
    monitor = "monitor"
    risk = "risk"


class ClassificationStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class Classification(Base, TimestampMixin):
    """AI enrichment output for one article — the record that turns a raw
    ingested item into intelligence.

    `sentiment_by_brand` is the key design point from the brief: sentiment
    is directed at each mentioned brand, not a single article-level score,
    e.g. {"Orange Botswana": "neutral", "BTC": "negative"}.
    """

    __tablename__ = "classifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    article_id: Mapped[str] = mapped_column(
        ForeignKey("articles.id"), unique=True, index=True
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)

    status: Mapped[ClassificationStatus] = mapped_column(
        Enum(ClassificationStatus), default=ClassificationStatus.pending
    )
    model_used: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sentiment_overall: Mapped[SentimentLabel | None] = mapped_column(
        Enum(SentimentLabel), nullable=True
    )
    sentiment_by_brand: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    entities: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    summary_exec: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_quotes: Mapped[list[str]] = mapped_column(JSON, default=list)
    why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)

    threat_tag: Mapped[ThreatTag | None] = mapped_column(Enum(ThreatTag), nullable=True)
    threat_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    classified_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    article: Mapped["Article"] = relationship(back_populates="classification")

    def __repr__(self) -> str:
        return f"Classification(article_id={self.article_id!r}, status={self.status!r})"
