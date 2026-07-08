"""Pulls one tenant-period's worth of classified coverage into the shapes
the Daily Brief needs: pillar sections (Client/Competitors/Regulator/
Sector), share of voice, sentiment shifts vs. the immediately preceding
period, and a watch-list of Risk/Opportunity items.

Deliberately has no AI dependency — everything here is arithmetic over
already-classified `Article`/`Classification` rows, so it's fully unit
tested without a model client. `ai/brief_synthesis.py` takes this data and
asks the synthesis model to write the prose (exec summary, recommended
actions) around it.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..models import Article, BriefType, ClassificationStatus, Tenant, ThreatTag, TopicKind

PILLAR_LABELS: dict[TopicKind, str] = {
    TopicKind.brand_watch: "Client",
    TopicKind.competitor: "Competitors",
    TopicKind.regulator: "Regulator",
    TopicKind.sector: "Sector",
    TopicKind.custom: "Other",
}


@dataclass
class PillarSection:
    name: str
    kind: TopicKind
    top_stories: list[Article]
    total_count: int


@dataclass
class SentimentShift:
    brand: str
    current: dict[str, int]
    previous: dict[str, int]


@dataclass
class WatchlistItem:
    article: Article
    threat_tag: ThreatTag
    rationale: str


@dataclass
class BriefData:
    tenant: Tenant
    period_start: dt.date
    period_end: dt.date
    articles: list[Article]
    pillars: list[PillarSection]
    share_of_voice: dict[str, int]
    sentiment_shifts: list[SentimentShift]
    watchlist: list[WatchlistItem]
    total_coverage_count: int = field(default=0)
    brief_type: BriefType = BriefType.daily


def _period_articles(session: Session, tenant: Tenant, start: dt.date, end: dt.date) -> list[Article]:
    published_date = func.coalesce(Article.published_at, Article.fetched_at)
    return (
        session.query(Article)
        .options(joinedload(Article.classification), joinedload(Article.topic))
        .filter(
            Article.tenant_id == tenant.id,
            published_date >= dt.datetime.combine(start, dt.time.min, tzinfo=dt.timezone.utc),
            published_date <= dt.datetime.combine(end, dt.time.max, tzinfo=dt.timezone.utc),
        )
        .all()
    )


def _brand_sentiment_counts(articles: list[Article]) -> dict[str, Counter]:
    result: dict[str, Counter] = defaultdict(Counter)
    for article in articles:
        c = article.classification
        if c is None or not c.sentiment_by_brand:
            continue
        for brand, sentiment in c.sentiment_by_brand.items():
            result[brand][sentiment] += 1
    return result


def build_brief_data(
    session: Session,
    tenant: Tenant,
    *,
    period_start: dt.date,
    period_end: dt.date,
    top_n_per_pillar: int = 3,
    brief_type: BriefType = BriefType.daily,
) -> BriefData:
    articles = _period_articles(session, tenant, period_start, period_end)
    classified = [
        a for a in articles
        if a.classification and a.classification.status == ClassificationStatus.success
    ]

    pillars = []
    for kind, name in PILLAR_LABELS.items():
        pillar_articles = [a for a in classified if a.topic.kind == kind]
        if not pillar_articles:
            continue
        top = sorted(
            pillar_articles, key=lambda a: (a.classification.relevance_score or 0.0), reverse=True
        )[:top_n_per_pillar]
        pillars.append(PillarSection(name=name, kind=kind, top_stories=top, total_count=len(pillar_articles)))

    sov: Counter[str] = Counter()
    for article in classified:
        c = article.classification
        brands = set(c.sentiment_by_brand.keys()) if c.sentiment_by_brand else set(
            (c.entities or {}).get("brands", [])
        )
        for brand in brands:
            sov[brand] += 1

    period_days = (period_end - period_start).days + 1
    prev_end = period_start - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=period_days - 1)
    prev_classified = [
        a for a in _period_articles(session, tenant, prev_start, prev_end)
        if a.classification and a.classification.status == ClassificationStatus.success
    ]

    current_counts = _brand_sentiment_counts(classified)
    previous_counts = _brand_sentiment_counts(prev_classified)
    all_brands = sorted(set(current_counts) | set(previous_counts))
    sentiment_shifts = [
        SentimentShift(
            brand=brand,
            current=dict(current_counts.get(brand, {})),
            previous=dict(previous_counts.get(brand, {})),
        )
        for brand in all_brands
    ]

    watchlist_articles = [
        a for a in classified
        if a.classification.threat_tag in (ThreatTag.risk, ThreatTag.opportunity)
    ]
    watchlist_articles.sort(
        key=lambda a: (
            a.classification.threat_tag != ThreatTag.risk,
            -(a.classification.relevance_score or 0.0),
        )
    )
    watchlist = [
        WatchlistItem(
            article=a, threat_tag=a.classification.threat_tag,
            rationale=a.classification.threat_rationale or "",
        )
        for a in watchlist_articles
    ]

    return BriefData(
        tenant=tenant,
        period_start=period_start,
        period_end=period_end,
        articles=classified,
        pillars=pillars,
        share_of_voice=dict(sov),
        sentiment_shifts=sentiment_shifts,
        watchlist=watchlist,
        total_coverage_count=len(articles),
        brief_type=brief_type,
    )
