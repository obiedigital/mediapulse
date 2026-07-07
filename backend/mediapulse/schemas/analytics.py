from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class KPIOut(BaseModel):
    period_start: dt.date
    period_end: dt.date
    total_articles: int
    classified_count: int
    pending_count: int
    error_count: int
    needs_review_count: int
    sentiment_breakdown: dict[str, int]
    avg_relevance: float | None
    opportunity_count: int
    monitor_count: int
    risk_count: int


class ShareOfVoicePointOut(BaseModel):
    date: dt.date
    brand: str
    mentions: int


class ShareOfVoiceOut(BaseModel):
    period_start: dt.date
    period_end: dt.date
    points: list[ShareOfVoicePointOut]
    methodology_note: str = (
        "Share of voice reflects mentions in ingested and classified coverage only — "
        "it is directional, not a full media-monitoring-universe measurement."
    )


class SentimentTrendPointOut(BaseModel):
    date: dt.date
    brand: str
    positive: int
    neutral: int
    negative: int


class TopicMixPointOut(BaseModel):
    topic_label: str
    category: str | None
    count: int


class PublicationStatOut(BaseModel):
    publication: str
    count: int


class BylineStatOut(BaseModel):
    byline: str
    publication: str | None
    count: int
