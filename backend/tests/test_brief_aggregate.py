import datetime as dt

from mediapulse.briefs.aggregate import build_brief_data
from mediapulse.models import (
    Article,
    Classification,
    ClassificationStatus,
    SentimentLabel,
    ThreatTag,
    Topic,
    TopicKind,
)


def _make_article(session, tenant, topic, *, title, published_at, content_hash,
                   category="telco", sentiment_overall=SentimentLabel.neutral,
                   sentiment_by_brand=None, threat_tag=ThreatTag.monitor,
                   threat_rationale="routine", relevance=0.7, classified=True):
    article = Article(
        tenant_id=tenant.id, topic_id=topic.id, publication="Mmegi Online",
        title=title, published_at=published_at, fetched_at=published_at,
        content_hash=content_hash, raw_text="body",
    )
    session.add(article)
    session.flush()
    if classified:
        session.add(Classification(
            article_id=article.id, tenant_id=tenant.id, status=ClassificationStatus.success,
            category=category, sentiment_overall=sentiment_overall,
            sentiment_by_brand=sentiment_by_brand or {}, threat_tag=threat_tag,
            threat_rationale=threat_rationale, relevance_score=relevance,
        ))
        session.flush()
    return article


def test_pillars_group_by_topic_kind(session, tenant):
    client_topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    competitor_topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add_all([client_topic, competitor_topic])
    session.flush()

    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    _make_article(session, tenant, client_topic, title="Orange story", published_at=day, content_hash="h1")
    _make_article(session, tenant, competitor_topic, title="BTC story", published_at=day, content_hash="h2")

    data = build_brief_data(session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10))

    pillar_names = {p.name for p in data.pillars}
    assert pillar_names == {"Client", "Competitors"}
    assert data.total_coverage_count == 2


def test_pillar_top_stories_ranked_by_relevance(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    _make_article(session, tenant, topic, title="Low relevance", published_at=day, content_hash="h1", relevance=0.2)
    _make_article(session, tenant, topic, title="High relevance", published_at=day, content_hash="h2", relevance=0.95)

    data = build_brief_data(session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10))

    client_pillar = next(p for p in data.pillars if p.name == "Client")
    assert client_pillar.top_stories[0].title == "High relevance"


def test_share_of_voice_counts_brand_mentions(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    _make_article(session, tenant, topic, title="A", published_at=day, content_hash="h1",
                   sentiment_by_brand={"BTC": "negative", "Orange Botswana": "neutral"})
    _make_article(session, tenant, topic, title="B", published_at=day, content_hash="h2",
                   sentiment_by_brand={"BTC": "neutral"})

    data = build_brief_data(session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10))

    assert data.share_of_voice == {"BTC": 2, "Orange Botswana": 1}


def test_sentiment_shift_compares_to_preceding_period(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add(topic)
    session.flush()

    prev_day = dt.datetime(2026, 6, 9, tzinfo=dt.timezone.utc)
    curr_day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    _make_article(session, tenant, topic, title="Prev", published_at=prev_day, content_hash="h1",
                   sentiment_by_brand={"BTC": "neutral"})
    _make_article(session, tenant, topic, title="Curr", published_at=curr_day, content_hash="h2",
                   sentiment_by_brand={"BTC": "negative"})

    data = build_brief_data(session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10))

    shift = next(s for s in data.sentiment_shifts if s.brand == "BTC")
    assert shift.current == {"negative": 1}
    assert shift.previous == {"neutral": 1}


def test_watchlist_includes_risk_and_opportunity_ranked_risk_first(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    _make_article(session, tenant, topic, title="Opportunity story", published_at=day, content_hash="h1",
                   threat_tag=ThreatTag.opportunity, relevance=0.99)
    _make_article(session, tenant, topic, title="Risk story", published_at=day, content_hash="h2",
                   threat_tag=ThreatTag.risk, relevance=0.5)
    _make_article(session, tenant, topic, title="Routine story", published_at=day, content_hash="h3",
                   threat_tag=ThreatTag.monitor)

    data = build_brief_data(session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10))

    assert [w.article.title for w in data.watchlist] == ["Risk story", "Opportunity story"]


def test_unclassified_articles_excluded_from_pillars_but_counted_in_total(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    _make_article(session, tenant, topic, title="Classified", published_at=day, content_hash="h1")
    _make_article(session, tenant, topic, title="Pending", published_at=day, content_hash="h2", classified=False)

    data = build_brief_data(session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10))

    assert data.total_coverage_count == 2
    client_pillar = next(p for p in data.pillars if p.name == "Client")
    assert client_pillar.total_count == 1
