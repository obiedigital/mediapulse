"""KPIs, share of voice, sentiment trend, topic mix, top publications, and
byline tracker — all computed over one tenant's classified/queued corpus
in a given period (default: trailing 30 days).
"""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ...models import Article, ArticleStatus, ClassificationStatus, Tenant, ThreatTag
from ...schemas import (
    BylineStatOut,
    KPIOut,
    PublicationStatOut,
    SentimentTrendPointOut,
    ShareOfVoiceOut,
    ShareOfVoicePointOut,
    TopicMixPointOut,
)
from ..deps import get_current_tenant, get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

DEFAULT_PERIOD_DAYS = 30


def _resolve_period(date_from: dt.date | None, date_to: dt.date | None) -> tuple[dt.date, dt.date]:
    end = date_to or dt.date.today()
    start = date_from or (end - dt.timedelta(days=DEFAULT_PERIOD_DAYS))
    return start, end


def _resolve_date(article: Article) -> dt.date:
    moment = article.published_at or article.fetched_at
    return moment.date()


def _articles_in_period(session: Session, tenant: Tenant, start: dt.date, end: dt.date) -> list[Article]:
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


def _article_brands(article: Article) -> set[str]:
    c = article.classification
    if c is None:
        return set()
    if c.sentiment_by_brand:
        return set(c.sentiment_by_brand.keys())
    brands = (c.entities or {}).get("brands", [])
    return set(brands) if brands else set()


@router.get("/kpis", response_model=KPIOut)
def kpis(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
):
    start, end = _resolve_period(date_from, date_to)
    articles = _articles_in_period(session, tenant, start, end)

    classified = [
        a for a in articles
        if a.classification and a.classification.status == ClassificationStatus.success
    ]
    sentiment_breakdown = Counter(
        a.classification.sentiment_overall.value
        for a in classified if a.classification.sentiment_overall
    )
    relevance_scores = [a.classification.relevance_score for a in classified if a.classification.relevance_score is not None]
    threat_counts = Counter(a.classification.threat_tag for a in classified if a.classification.threat_tag)

    return KPIOut(
        period_start=start,
        period_end=end,
        total_articles=len(articles),
        classified_count=len(classified),
        pending_count=sum(1 for a in articles if a.status == ArticleStatus.new),
        error_count=sum(1 for a in articles if a.status == ArticleStatus.error),
        needs_review_count=sum(1 for a in articles if a.status == ArticleStatus.needs_review),
        sentiment_breakdown=dict(sentiment_breakdown),
        avg_relevance=sum(relevance_scores) / len(relevance_scores) if relevance_scores else None,
        opportunity_count=threat_counts.get(ThreatTag.opportunity, 0),
        monitor_count=threat_counts.get(ThreatTag.monitor, 0),
        risk_count=threat_counts.get(ThreatTag.risk, 0),
    )


@router.get("/share-of-voice", response_model=ShareOfVoiceOut)
def share_of_voice(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
):
    start, end = _resolve_period(date_from, date_to)
    articles = _articles_in_period(session, tenant, start, end)

    tally: Counter[tuple[dt.date, str]] = Counter()
    for article in articles:
        date = _resolve_date(article)
        for brand in _article_brands(article):
            tally[(date, brand)] += 1

    points = [
        ShareOfVoicePointOut(date=date, brand=brand, mentions=count)
        for (date, brand), count in sorted(tally.items())
    ]
    return ShareOfVoiceOut(period_start=start, period_end=end, points=points)


@router.get("/sentiment-trend", response_model=list[SentimentTrendPointOut])
def sentiment_trend(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
):
    start, end = _resolve_period(date_from, date_to)
    articles = _articles_in_period(session, tenant, start, end)

    tally: dict[tuple[dt.date, str], Counter] = defaultdict(Counter)
    for article in articles:
        c = article.classification
        if c is None or not c.sentiment_by_brand:
            continue
        date = _resolve_date(article)
        for brand, sentiment in c.sentiment_by_brand.items():
            tally[(date, brand)][sentiment] += 1

    return [
        SentimentTrendPointOut(
            date=date, brand=brand,
            positive=counts.get("positive", 0),
            neutral=counts.get("neutral", 0),
            negative=counts.get("negative", 0),
        )
        for (date, brand), counts in sorted(tally.items())
    ]


@router.get("/topic-mix", response_model=list[TopicMixPointOut])
def topic_mix(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
):
    start, end = _resolve_period(date_from, date_to)
    articles = _articles_in_period(session, tenant, start, end)

    tally: Counter[tuple[str, str | None]] = Counter()
    for article in articles:
        category = article.classification.category if article.classification else None
        tally[(article.topic.label, category)] += 1

    return [
        TopicMixPointOut(topic_label=label, category=category, count=count)
        for (label, category), count in sorted(tally.items(), key=lambda kv: -kv[1])
    ]


@router.get("/top-publications", response_model=list[PublicationStatOut])
def top_publications(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int = Query(10, ge=1, le=50),
):
    start, end = _resolve_period(date_from, date_to)
    articles = _articles_in_period(session, tenant, start, end)

    tally = Counter(a.publication for a in articles)
    return [
        PublicationStatOut(publication=pub, count=count)
        for pub, count in tally.most_common(limit)
    ]


@router.get("/bylines", response_model=list[BylineStatOut])
def bylines(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int = Query(10, ge=1, le=50),
):
    start, end = _resolve_period(date_from, date_to)
    articles = _articles_in_period(session, tenant, start, end)

    counts: Counter[str] = Counter()
    publications: dict[str, Counter] = defaultdict(Counter)
    for article in articles:
        if not article.byline:
            continue
        counts[article.byline] += 1
        publications[article.byline][article.publication] += 1

    return [
        BylineStatOut(
            byline=byline,
            publication=publications[byline].most_common(1)[0][0] if publications[byline] else None,
            count=count,
        )
        for byline, count in counts.most_common(limit)
    ]
