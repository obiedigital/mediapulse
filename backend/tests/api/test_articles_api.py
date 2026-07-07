import datetime as dt

from mediapulse.models import (
    Article,
    ArticleStatus,
    Classification,
    ClassificationStatus,
    SentimentLabel,
    Tenant,
    ThreatTag,
    Topic,
    TopicKind,
)

from .conftest import auth_headers


def _make_article(session, tenant, topic, *, title, published_at, content_hash,
                   status=ArticleStatus.classified, classification_kwargs=None, byline=None):
    article = Article(
        tenant_id=tenant.id, topic_id=topic.id, publication="Mmegi Online",
        title=title, byline=byline, published_at=published_at, fetched_at=published_at,
        content_hash=content_hash, raw_text="Body text " * 10, status=status,
    )
    session.add(article)
    session.flush()
    if classification_kwargs is not None:
        session.add(Classification(article_id=article.id, tenant_id=tenant.id,
                                    status=ClassificationStatus.success, **classification_kwargs))
        session.flush()
    return article


def test_articles_list_requires_auth(client):
    response = client.get("/articles")
    assert response.status_code == 401


def test_articles_list_returns_tenant_scoped_data(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    _make_article(session, tenant, topic, title="Story A", published_at=day, content_hash="h1")

    headers = auth_headers(client, session, tenant)
    response = client.get("/articles", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Story A"
    assert body["items"][0]["published_at"].startswith("2026-06-10")


def test_articles_list_never_returns_null_published_at(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    now = dt.datetime.now(dt.timezone.utc)
    article = Article(
        tenant_id=tenant.id, topic_id=topic.id, publication="Mmegi",
        title="No published date", published_at=None, fetched_at=now,
        content_hash="h-null", raw_text="body",
    )
    session.add(article)
    session.flush()

    headers = auth_headers(client, session, tenant)
    response = client.get("/articles", headers=headers)

    item = response.json()["items"][0]
    assert item["published_at"] is not None
    assert item["published_at_confidence"] == "low"


def test_articles_isolated_across_tenants(client, session, tenant):
    other_tenant = Tenant(slug="other-bank", name="Other Bank")
    session.add(other_tenant)
    session.flush()
    topic_a = Topic(tenant_id=tenant.id, label="Orange watch", kind=TopicKind.brand_watch)
    topic_b = Topic(tenant_id=other_tenant.id, label="Bank watch", kind=TopicKind.brand_watch)
    session.add_all([topic_a, topic_b])
    session.flush()

    now = dt.datetime.now(dt.timezone.utc)
    _make_article(session, tenant, topic_a, title="Orange story", published_at=now, content_hash="ha")
    _make_article(session, other_tenant, topic_b, title="Bank story", published_at=now, content_hash="hb")

    headers = auth_headers(client, session, tenant, email="analyst@orange.bw")
    response = client.get("/articles", headers=headers)

    titles = {item["title"] for item in response.json()["items"]}
    assert titles == {"Orange story"}


def test_tenant_scoped_user_cannot_override_tenant_query_param(client, session, tenant):
    other_tenant = Tenant(slug="other-bank", name="Other Bank")
    session.add(other_tenant)
    session.flush()

    headers = auth_headers(client, session, tenant, email="analyst@orange.bw")
    response = client.get("/articles", params={"tenant": "other-bank"}, headers=headers)

    assert response.status_code == 403


def test_articles_filter_by_sentiment_and_category(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add(topic)
    session.flush()
    now = dt.datetime.now(dt.timezone.utc)
    _make_article(
        session, tenant, topic, title="Negative telco story", published_at=now, content_hash="h-neg",
        classification_kwargs={
            "category": "telco", "sentiment_overall": SentimentLabel.negative,
            "sentiment_by_brand": {"BTC": "negative"}, "threat_tag": ThreatTag.risk,
        },
    )
    _make_article(
        session, tenant, topic, title="Neutral sport story", published_at=now, content_hash="h-neu",
        classification_kwargs={
            "category": "sport", "sentiment_overall": SentimentLabel.neutral,
            "sentiment_by_brand": {}, "threat_tag": ThreatTag.monitor,
        },
    )

    headers = auth_headers(client, session, tenant)
    response = client.get("/articles", params={"sentiment": "negative"}, headers=headers)
    assert [i["title"] for i in response.json()["items"]] == ["Negative telco story"]

    response = client.get("/articles", params={"category": "sport"}, headers=headers)
    assert [i["title"] for i in response.json()["items"]] == ["Neutral sport story"]

    response = client.get("/articles", params={"brand": "BTC"}, headers=headers)
    assert [i["title"] for i in response.json()["items"]] == ["Negative telco story"]


def test_articles_pagination(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange watch", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    now = dt.datetime.now(dt.timezone.utc)
    for i in range(5):
        _make_article(session, tenant, topic, title=f"Story {i}", published_at=now, content_hash=f"h{i}")

    headers = auth_headers(client, session, tenant)
    response = client.get("/articles", params={"limit": 2, "offset": 0}, headers=headers)
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2


def test_article_detail_includes_classification(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange watch", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    now = dt.datetime.now(dt.timezone.utc)
    article = _make_article(
        session, tenant, topic, title="Detailed story", published_at=now, content_hash="h-detail",
        classification_kwargs={
            "category": "telco", "sentiment_overall": SentimentLabel.neutral,
            "summary_exec": "A two sentence summary.", "why_it_matters": "Because it matters.",
            "threat_tag": ThreatTag.monitor, "threat_rationale": "routine",
        },
    )

    headers = auth_headers(client, session, tenant)
    response = client.get(f"/articles/{article.id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["summary_exec"] == "A two sentence summary."
    assert body["threat_tag"] == "monitor"


def test_article_detail_404_for_unknown_id(client, session, tenant):
    headers = auth_headers(client, session, tenant)
    response = client.get("/articles/does-not-exist", headers=headers)
    assert response.status_code == 404


def test_articles_csv_export(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange watch", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    now = dt.datetime.now(dt.timezone.utc)
    _make_article(session, tenant, topic, title="CSV Story", published_at=now, content_hash="h-csv")

    headers = auth_headers(client, session, tenant)
    response = client.get("/articles/export.csv", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "CSV Story" in response.text
