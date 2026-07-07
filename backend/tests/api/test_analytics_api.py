import datetime as dt

from mediapulse.models import (
    Article,
    Classification,
    ClassificationStatus,
    SentimentLabel,
    ThreatTag,
    Topic,
    TopicKind,
)

from .conftest import auth_headers


def _make_classified_article(session, tenant, topic, *, title, publication, byline,
                              published_at, content_hash, category, sentiment_overall,
                              sentiment_by_brand, threat_tag, relevance_score=0.8):
    article = Article(
        tenant_id=tenant.id, topic_id=topic.id, publication=publication, title=title,
        byline=byline, published_at=published_at, fetched_at=published_at,
        content_hash=content_hash, raw_text="body",
    )
    session.add(article)
    session.flush()
    session.add(Classification(
        article_id=article.id, tenant_id=tenant.id, status=ClassificationStatus.success,
        category=category, sentiment_overall=sentiment_overall,
        sentiment_by_brand=sentiment_by_brand, threat_tag=threat_tag,
        relevance_score=relevance_score,
    ))
    session.flush()
    return article


def test_kpis_counts_and_averages(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    _make_classified_article(
        session, tenant, topic, title="A", publication="Mmegi", byline="By A",
        published_at=day, content_hash="h1", category="telco",
        sentiment_overall=SentimentLabel.negative, sentiment_by_brand={"BTC": "negative"},
        threat_tag=ThreatTag.risk, relevance_score=0.9,
    )
    _make_classified_article(
        session, tenant, topic, title="B", publication="The Voice", byline="By B",
        published_at=day, content_hash="h2", category="telco",
        sentiment_overall=SentimentLabel.neutral, sentiment_by_brand={"Orange Botswana": "neutral"},
        threat_tag=ThreatTag.monitor, relevance_score=0.5,
    )

    headers = auth_headers(client, session, tenant)
    response = client.get(
        "/analytics/kpis",
        params={"date_from": "2026-06-01", "date_to": "2026-06-30"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_articles"] == 2
    assert body["classified_count"] == 2
    assert body["sentiment_breakdown"] == {"negative": 1, "neutral": 1}
    assert body["risk_count"] == 1
    assert body["monitor_count"] == 1
    assert body["avg_relevance"] == 0.7


def test_share_of_voice_tallies_brand_mentions_per_day(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add(topic)
    session.flush()
    day1 = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    day2 = dt.datetime(2026, 6, 11, tzinfo=dt.timezone.utc)

    _make_classified_article(
        session, tenant, topic, title="A", publication="Mmegi", byline=None,
        published_at=day1, content_hash="h1", category="telco",
        sentiment_overall=SentimentLabel.negative,
        sentiment_by_brand={"BTC": "negative", "Orange Botswana": "neutral"},
        threat_tag=ThreatTag.risk,
    )
    _make_classified_article(
        session, tenant, topic, title="B", publication="The Voice", byline=None,
        published_at=day2, content_hash="h2", category="telco",
        sentiment_overall=SentimentLabel.neutral, sentiment_by_brand={"BTC": "neutral"},
        threat_tag=ThreatTag.monitor,
    )

    headers = auth_headers(client, session, tenant)
    response = client.get(
        "/analytics/share-of-voice",
        params={"date_from": "2026-06-01", "date_to": "2026-06-30"},
        headers=headers,
    )

    points = {(p["date"], p["brand"]): p["mentions"] for p in response.json()["points"]}
    assert points[("2026-06-10", "BTC")] == 1
    assert points[("2026-06-10", "Orange Botswana")] == 1
    assert points[("2026-06-11", "BTC")] == 1


def test_top_publications_and_bylines(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange watch", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    for i in range(3):
        _make_classified_article(
            session, tenant, topic, title=f"Mmegi story {i}", publication="Mmegi Online",
            byline="By Jane Doe", published_at=day, content_hash=f"pub-{i}",
            category="telco", sentiment_overall=SentimentLabel.neutral,
            sentiment_by_brand={}, threat_tag=ThreatTag.monitor,
        )
    _make_classified_article(
        session, tenant, topic, title="Voice story", publication="The Voice",
        byline="By John Smith", published_at=day, content_hash="pub-voice",
        category="telco", sentiment_overall=SentimentLabel.neutral,
        sentiment_by_brand={}, threat_tag=ThreatTag.monitor,
    )

    headers = auth_headers(client, session, tenant)

    pubs = client.get(
        "/analytics/top-publications",
        params={"date_from": "2026-06-01", "date_to": "2026-06-30"},
        headers=headers,
    ).json()
    assert pubs[0] == {"publication": "Mmegi Online", "count": 3}

    byline_stats = client.get(
        "/analytics/bylines",
        params={"date_from": "2026-06-01", "date_to": "2026-06-30"},
        headers=headers,
    ).json()
    assert byline_stats[0]["byline"] == "By Jane Doe"
    assert byline_stats[0]["count"] == 3


def test_topic_mix_groups_by_topic_and_category(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="BOCRA & regulation", kind=TopicKind.regulator)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    _make_classified_article(
        session, tenant, topic, title="Reg story", publication="Mmegi", byline=None,
        published_at=day, content_hash="tm-1", category="regulator",
        sentiment_overall=SentimentLabel.neutral, sentiment_by_brand={}, threat_tag=ThreatTag.monitor,
    )

    headers = auth_headers(client, session, tenant)
    response = client.get(
        "/analytics/topic-mix",
        params={"date_from": "2026-06-01", "date_to": "2026-06-30"},
        headers=headers,
    )
    body = response.json()
    assert body[0]["topic_label"] == "BOCRA & regulation"
    assert body[0]["category"] == "regulator"
    assert body[0]["count"] == 1
