"""Article response schemas.

`published_at` is always a concrete datetime here — never optional. The
legacy dashboard's "Invalid Date" bug (M0 defect #4) came from serializing
a nullable DB column straight to JSON; the router resolves
`published_at or fetched_at` before constructing this schema, so a missing
date simply can't reach the frontend. `published_at_confidence` carries
the caveat instead.
"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class ArticleListItemOut(BaseModel):
    id: str
    title: str
    publication: str
    url: str | None
    byline: str | None
    topic_label: str
    published_at: dt.datetime
    published_at_confidence: str
    status: str
    is_advert: bool
    pickup_count: int
    category: str | None
    sentiment_overall: str | None
    threat_tag: str | None
    relevance_score: float | None


class ArticleListResponse(BaseModel):
    items: list[ArticleListItemOut]
    total: int
    limit: int
    offset: int


class ArticleDetailOut(BaseModel):
    id: str
    title: str
    publication: str
    url: str | None
    byline: str | None
    section: str | None
    page_number: int | None
    topic_label: str
    published_at: dt.datetime
    published_at_confidence: str
    fetched_at: dt.datetime
    status: str
    is_advert: bool
    pickup_count: int
    raw_text: str

    # classification (all None until AI enrichment has run)
    category: str | None
    relevance_score: float | None
    sentiment_overall: str | None
    sentiment_by_brand: dict[str, str]
    entities: dict[str, list[str]]
    summary_exec: str | None
    key_quotes: list[str]
    why_it_matters: str | None
    threat_tag: str | None
    threat_rationale: str | None
    model_used: str | None
    classified_at: dt.datetime | None
