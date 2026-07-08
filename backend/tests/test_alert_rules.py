import datetime as dt

from mediapulse.alerts.rules import evaluate_article_alerts, evaluate_volume_spike
from mediapulse.models import (
    Alert,
    AlertType,
    Article,
    ArticleStatus,
    Classification,
    ClassificationStatus,
    SentimentLabel,
    ThreatTag,
    Topic,
    TopicKind,
)


def _make_topic(session, tenant, kind, label=None):
    topic = Topic(tenant_id=tenant.id, label=label or f"{kind.value} topic", kind=kind)
    session.add(topic)
    session.flush()
    return topic


def _make_article(session, tenant, topic, *, title, content_hash, sentiment_by_brand=None,
                   classified=True, published_at=None):
    published_at = published_at or dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    article = Article(
        tenant_id=tenant.id, topic_id=topic.id, publication="Mmegi Online", title=title,
        published_at=published_at, fetched_at=published_at, content_hash=content_hash,
        raw_text="body", status=ArticleStatus.classified if classified else ArticleStatus.new,
    )
    session.add(article)
    session.flush()
    if classified:
        session.add(Classification(
            article_id=article.id, tenant_id=tenant.id, status=ClassificationStatus.success,
            sentiment_overall=SentimentLabel.neutral, sentiment_by_brand=sentiment_by_brand or {},
            threat_tag=ThreatTag.monitor,
        ))
        session.flush()
    return article


def test_negative_sentiment_on_client_brand_triggers_alert(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.brand_watch)
    article = _make_article(session, tenant, topic, title="Orange service outage frustrates customers",
                             content_hash="h1", sentiment_by_brand={"Orange Botswana": "negative"})

    alerts = evaluate_article_alerts(session, tenant, article)

    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.negative_sentiment


def test_positive_sentiment_on_client_brand_no_alert(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.brand_watch)
    article = _make_article(session, tenant, topic, title="Orange wins award", content_hash="h2",
                             sentiment_by_brand={"Orange Botswana": "positive"})

    assert evaluate_article_alerts(session, tenant, article) == []


def test_competitor_launch_keyword_triggers_alert(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.competitor)
    article = _make_article(session, tenant, topic, title="BTC launches new prepaid bundle", content_hash="h3")

    alerts = evaluate_article_alerts(session, tenant, article)

    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.competitor_launch


def test_competitor_story_without_launch_keyword_no_alert(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.competitor)
    article = _make_article(session, tenant, topic, title="BTC reports quarterly earnings", content_hash="h4")

    assert evaluate_article_alerts(session, tenant, article) == []


def test_any_regulator_story_triggers_alert(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.regulator)
    article = _make_article(session, tenant, topic, title="BOCRA issues new directive", content_hash="h5")

    alerts = evaluate_article_alerts(session, tenant, article)

    assert len(alerts) == 1
    assert alerts[0].alert_type == AlertType.regulator_announcement


def test_unclassified_article_produces_no_alerts(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.regulator)
    article = _make_article(session, tenant, topic, title="BOCRA issues new directive", content_hash="h6",
                             classified=False)

    assert evaluate_article_alerts(session, tenant, article) == []


def test_alert_is_idempotent_on_rerun(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.brand_watch)
    article = _make_article(session, tenant, topic, title="Orange outage anger", content_hash="h7",
                             sentiment_by_brand={"Orange Botswana": "negative"})

    first = evaluate_article_alerts(session, tenant, article)
    second = evaluate_article_alerts(session, tenant, article)

    assert len(first) == 1
    assert second == []
    assert session.query(Alert).filter_by(article_id=article.id).count() == 1


def test_volume_spike_detected_above_threshold(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.sector)
    baseline_day = dt.datetime(2026, 6, 9, tzinfo=dt.timezone.utc)
    _make_article(session, tenant, topic, title="Routine story", content_hash="base1", published_at=baseline_day)

    spike_day = dt.date(2026, 6, 10)
    spike_dt = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    for i in range(5):
        _make_article(session, tenant, topic, title=f"Spike story {i}", content_hash=f"spike{i}", published_at=spike_dt)

    alert = evaluate_volume_spike(session, tenant, reference_date=spike_day, baseline_days=7)

    assert alert is not None
    assert alert.alert_type == AlertType.volume_spike


def test_volume_spike_not_detected_below_threshold(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.sector)
    day = dt.date(2026, 6, 10)
    _make_article(session, tenant, topic, title="One story", content_hash="one",
                  published_at=dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc))

    alert = evaluate_volume_spike(session, tenant, reference_date=day, min_baseline_count=3)

    assert alert is None


def test_volume_spike_idempotent_same_day(session, tenant):
    topic = _make_topic(session, tenant, TopicKind.sector)
    spike_day = dt.date(2026, 6, 10)
    spike_dt = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    for i in range(5):
        _make_article(session, tenant, topic, title=f"Spike {i}", content_hash=f"s{i}", published_at=spike_dt)

    first = evaluate_volume_spike(session, tenant, reference_date=spike_day)
    second = evaluate_volume_spike(session, tenant, reference_date=spike_day)

    assert first is not None
    assert second is None
