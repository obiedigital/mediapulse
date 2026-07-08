"""Alert rule detection.

Article-scoped rules (negative sentiment about the tenant's own brand,
competitor launch, regulator announcement) run once per article right
after classification succeeds — `ai/classify.py` calls
`evaluate_article_alerts` immediately after a successful classification,
so an alert-worthy story is flagged the moment it's enriched rather than
on some later batch schedule. The volume-spike rule is day-scoped (not a
property of any one article) and is checked separately via
`evaluate_volume_spike` — see `mediapulse alerts`.

Idempotent: article-scoped alerts are keyed on (article_id, alert_type),
so reclassifying an article (`--reprocess-errors`) never double-alerts.
Volume-spike alerts are keyed on (tenant_id, alert_type, day).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Alert, AlertType, Article, ClassificationStatus, Tenant, TopicKind

_LAUNCH_KEYWORDS = ("launch", "unveil", "introduce", "rolls out", "debut")

DEFAULT_BASELINE_DAYS = 7
DEFAULT_SPIKE_MULTIPLIER = 2.0
DEFAULT_MIN_BASELINE_COUNT = 3


def _has_existing_alert(session: Session, article_id: str, alert_type: AlertType) -> bool:
    return (
        session.query(Alert).filter_by(article_id=article_id, alert_type=alert_type).first()
        is not None
    )


def evaluate_article_alerts(session: Session, tenant: Tenant, article: Article) -> list[Alert]:
    c = article.classification
    if c is None or c.status != ClassificationStatus.success:
        return []

    candidates: list[Alert] = []

    if article.topic.kind == TopicKind.brand_watch and c.sentiment_by_brand:
        if any(sentiment == "negative" for sentiment in c.sentiment_by_brand.values()):
            if not _has_existing_alert(session, article.id, AlertType.negative_sentiment):
                candidates.append(Alert(
                    tenant_id=tenant.id, article_id=article.id,
                    alert_type=AlertType.negative_sentiment,
                    message=f'Negative coverage of {tenant.name}: "{article.title}" ({article.publication}).',
                ))

    if article.topic.kind == TopicKind.competitor:
        title_lower = article.title.lower()
        if any(keyword in title_lower for keyword in _LAUNCH_KEYWORDS):
            if not _has_existing_alert(session, article.id, AlertType.competitor_launch):
                candidates.append(Alert(
                    tenant_id=tenant.id, article_id=article.id,
                    alert_type=AlertType.competitor_launch,
                    message=f'Competitor launch signal: "{article.title}" ({article.publication}).',
                ))

    if article.topic.kind == TopicKind.regulator:
        if not _has_existing_alert(session, article.id, AlertType.regulator_announcement):
            candidates.append(Alert(
                tenant_id=tenant.id, article_id=article.id,
                alert_type=AlertType.regulator_announcement,
                message=f'Regulator news: "{article.title}" ({article.publication}).',
            ))

    for alert in candidates:
        session.add(alert)
    if candidates:
        session.flush()
    return candidates


def _count_articles_on(session: Session, tenant: Tenant, day: dt.date) -> int:
    published_date = func.coalesce(Article.published_at, Article.fetched_at)
    return (
        session.query(Article)
        .filter(
            Article.tenant_id == tenant.id,
            published_date >= dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc),
            published_date <= dt.datetime.combine(day, dt.time.max, tzinfo=dt.timezone.utc),
        )
        .count()
    )


def evaluate_volume_spike(
    session: Session,
    tenant: Tenant,
    *,
    reference_date: dt.date | None = None,
    baseline_days: int = DEFAULT_BASELINE_DAYS,
    spike_multiplier: float = DEFAULT_SPIKE_MULTIPLIER,
    min_baseline_count: int = DEFAULT_MIN_BASELINE_COUNT,
) -> Alert | None:
    reference_date = reference_date or dt.date.today()

    today_count = _count_articles_on(session, tenant, reference_date)
    baseline_counts = [
        _count_articles_on(session, tenant, reference_date - dt.timedelta(days=offset))
        for offset in range(1, baseline_days + 1)
    ]
    baseline_avg = sum(baseline_counts) / len(baseline_counts) if baseline_counts else 0.0
    threshold = max(min_baseline_count, baseline_avg * spike_multiplier)

    if today_count < threshold:
        return None

    day_start = dt.datetime.combine(reference_date, dt.time.min, tzinfo=dt.timezone.utc)
    already_flagged = (
        session.query(Alert)
        .filter(
            Alert.tenant_id == tenant.id,
            Alert.alert_type == AlertType.volume_spike,
            Alert.created_at >= day_start,
        )
        .first()
    )
    if already_flagged is not None:
        return None

    alert = Alert(
        tenant_id=tenant.id,
        article_id=None,
        alert_type=AlertType.volume_spike,
        message=(
            f"Coverage volume spike: {today_count} items on {reference_date.isoformat()} "
            f"vs. a {baseline_days}-day average of {baseline_avg:.1f}."
        ),
    )
    session.add(alert)
    session.flush()
    return alert
