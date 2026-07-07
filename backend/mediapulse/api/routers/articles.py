"""Story feed + story detail + CSV export.

`_resolve_published_at` is the one place that turns a possibly-null
`published_at` into a guaranteed datetime before it reaches a response
schema — see `schemas/articles.py` for why that matters.

Filtering note: brand filtering reads JSON columns
(`sentiment_by_brand`/`entities`), which isn't portable to do efficiently
across both SQLite (dev) and Postgres (prod) with the SQLAlchemy core
query API, so it's applied in Python after the SQL-level filters run. Fine
at this stage's data volumes; revisit with Postgres jsonb operators if a
tenant's corpus grows enough for this to matter.
"""
from __future__ import annotations

import csv
import datetime as dt
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ...models import Article, ArticleStatus, Classification, SentimentLabel, Tenant
from ...schemas import ArticleDetailOut, ArticleListItemOut, ArticleListResponse
from ..deps import get_current_tenant, get_db

router = APIRouter(prefix="/articles", tags=["articles"])


def _resolve_published_at(article: Article) -> tuple[dt.datetime, str]:
    if article.published_at is not None:
        return article.published_at, article.published_at_confidence
    return article.fetched_at, "low"


def _filtered_articles(
    session: Session,
    tenant: Tenant,
    *,
    date_from: dt.date | None,
    date_to: dt.date | None,
    publication: str | None,
    sentiment: str | None,
    category: str | None,
    status: str | None,
    brand: str | None,
    search: str | None,
) -> list[Article]:
    query = (
        session.query(Article)
        .options(joinedload(Article.classification), joinedload(Article.topic), joinedload(Article.story_cluster))
        .outerjoin(Classification, Classification.article_id == Article.id)
        .filter(Article.tenant_id == tenant.id)
    )

    if publication:
        query = query.filter(Article.publication == publication)
    if search:
        query = query.filter(Article.title.ilike(f"%{search}%"))
    if status:
        try:
            query = query.filter(Article.status == ArticleStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status {status!r}") from None
    if category:
        query = query.filter(Classification.category == category)
    if sentiment:
        try:
            query = query.filter(Classification.sentiment_overall == SentimentLabel(sentiment))
        except ValueError:
            raise HTTPException(400, f"Invalid sentiment {sentiment!r}") from None

    published_date = func.coalesce(Article.published_at, Article.fetched_at)
    if date_from:
        query = query.filter(published_date >= dt.datetime.combine(date_from, dt.time.min, tzinfo=dt.timezone.utc))
    if date_to:
        query = query.filter(published_date <= dt.datetime.combine(date_to, dt.time.max, tzinfo=dt.timezone.utc))

    query = query.order_by(published_date.desc())
    articles = query.all()

    if brand:
        def mentions_brand(article: Article) -> bool:
            c = article.classification
            if c is None:
                return False
            if brand in (c.sentiment_by_brand or {}):
                return True
            return brand in (c.entities or {}).get("brands", [])

        articles = [a for a in articles if mentions_brand(a)]

    return articles


def _to_list_item(article: Article) -> ArticleListItemOut:
    published_at, confidence = _resolve_published_at(article)
    c = article.classification
    pickup_count = article.story_cluster.pickup_count if article.story_cluster else 1
    return ArticleListItemOut(
        id=article.id,
        title=article.title,
        publication=article.publication,
        url=article.url,
        byline=article.byline,
        topic_label=article.topic.label,
        published_at=published_at,
        published_at_confidence=confidence,
        status=article.status.value,
        is_advert=article.is_advert,
        pickup_count=pickup_count,
        category=c.category if c else None,
        sentiment_overall=c.sentiment_overall.value if c and c.sentiment_overall else None,
        threat_tag=c.threat_tag.value if c and c.threat_tag else None,
        relevance_score=c.relevance_score if c else None,
    )


@router.get("/export.csv")
def export_articles_csv(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    publication: str | None = None,
    sentiment: str | None = None,
    category: str | None = None,
    status: str | None = None,
    brand: str | None = None,
    search: str | None = None,
):
    articles = _filtered_articles(
        session, tenant, date_from=date_from, date_to=date_to, publication=publication,
        sentiment=sentiment, category=category, status=status, brand=brand, search=search,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "title", "publication", "byline", "url", "published_at",
        "published_at_confidence", "status", "category", "sentiment_overall",
        "threat_tag", "relevance_score", "pickup_count",
    ])
    for article in articles:
        item = _to_list_item(article)
        writer.writerow([
            item.id, item.title, item.publication, item.byline or "", item.url or "",
            item.published_at.isoformat(), item.published_at_confidence, item.status,
            item.category or "", item.sentiment_overall or "", item.threat_tag or "",
            item.relevance_score if item.relevance_score is not None else "", item.pickup_count,
        ])
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=articles.csv"},
    )


@router.get("", response_model=ArticleListResponse)
def list_articles(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    publication: str | None = None,
    sentiment: str | None = None,
    category: str | None = None,
    status: str | None = None,
    brand: str | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    articles = _filtered_articles(
        session, tenant, date_from=date_from, date_to=date_to, publication=publication,
        sentiment=sentiment, category=category, status=status, brand=brand, search=search,
    )
    total = len(articles)
    page = articles[offset : offset + limit]
    return ArticleListResponse(
        items=[_to_list_item(a) for a in page], total=total, limit=limit, offset=offset
    )


@router.get("/{article_id}", response_model=ArticleDetailOut)
def get_article(
    article_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
):
    article = (
        session.query(Article)
        .options(joinedload(Article.classification), joinedload(Article.topic), joinedload(Article.story_cluster))
        .filter_by(id=article_id, tenant_id=tenant.id)
        .one_or_none()
    )
    if article is None:
        raise HTTPException(404, "Article not found")

    published_at, confidence = _resolve_published_at(article)
    c = article.classification
    pickup_count = article.story_cluster.pickup_count if article.story_cluster else 1

    return ArticleDetailOut(
        id=article.id,
        title=article.title,
        publication=article.publication,
        url=article.url,
        byline=article.byline,
        section=article.section,
        page_number=article.page_number,
        topic_label=article.topic.label,
        published_at=published_at,
        published_at_confidence=confidence,
        fetched_at=article.fetched_at,
        status=article.status.value,
        is_advert=article.is_advert,
        pickup_count=pickup_count,
        raw_text=article.raw_text,
        category=c.category if c else None,
        relevance_score=c.relevance_score if c else None,
        sentiment_overall=c.sentiment_overall.value if c and c.sentiment_overall else None,
        sentiment_by_brand=c.sentiment_by_brand if c else {},
        entities=c.entities if c else {},
        summary_exec=c.summary_exec if c else None,
        key_quotes=c.key_quotes if c else [],
        why_it_matters=c.why_it_matters if c else None,
        threat_tag=c.threat_tag.value if c and c.threat_tag else None,
        threat_rationale=c.threat_rationale if c else None,
        model_used=c.model_used if c else None,
        classified_at=c.classified_at if c else None,
    )
