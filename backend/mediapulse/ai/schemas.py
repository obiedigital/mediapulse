"""Strict schema for the classification model's JSON output.

Every field the `Classification` table stores is required here too (with
sane defaults only where the table also defaults), so a response that's
missing a field fails validation loudly and gets retried rather than
silently landing in the database half-populated.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..models.classification import SentimentLabel, ThreatTag


class EntityList(BaseModel):
    brands: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    organisations: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    relevance_score: float = Field(ge=0.0, le=1.0)
    category: str
    sentiment_overall: SentimentLabel
    # brand name -> sentiment directed at that brand specifically, e.g.
    # {"Orange Botswana": "neutral", "BTC": "negative"} for one article.
    sentiment_by_brand: dict[str, SentimentLabel] = Field(default_factory=dict)
    entities: EntityList = Field(default_factory=EntityList)
    summary_exec: str
    key_quotes: list[str] = Field(default_factory=list)
    why_it_matters: str
    threat_tag: ThreatTag
    threat_rationale: str
