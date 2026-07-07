import datetime as dt

from mediapulse.models import (
    Article,
    ArticleStatus,
    Classification,
    ClassificationStatus,
    SentimentLabel,
    Topic,
    TopicKind,
)


def test_tenant_scoped_topic_and_article(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()

    now = dt.datetime.now(dt.timezone.utc)
    article = Article(
        tenant_id=tenant.id,
        topic_id=topic.id,
        publication="Mmegi Online",
        title="Orange Botswana launches new data bundle",
        published_at=now,
        fetched_at=now,
        content_hash="abc123",
        raw_text="Full article body...",
    )
    session.add(article)
    session.flush()

    fetched = session.query(Article).filter_by(tenant_id=tenant.id).one()
    assert fetched.status == ArticleStatus.new
    assert fetched.topic.label == "Orange Botswana (brand watch)"


def test_classification_sentiment_is_per_brand_not_article_wide(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add(topic)
    session.flush()

    now = dt.datetime.now(dt.timezone.utc)
    article = Article(
        tenant_id=tenant.id,
        topic_id=topic.id,
        publication="The Voice",
        title="BTC cuts data prices as Orange holds steady",
        published_at=now,
        fetched_at=now,
        content_hash="def456",
        raw_text="...",
    )
    session.add(article)
    session.flush()

    classification = Classification(
        article_id=article.id,
        tenant_id=tenant.id,
        status=ClassificationStatus.success,
        sentiment_overall=SentimentLabel.neutral,
        sentiment_by_brand={"Orange Botswana": "neutral", "BTC": "negative"},
    )
    session.add(classification)
    session.flush()

    saved = session.query(Classification).filter_by(article_id=article.id).one()
    assert saved.sentiment_by_brand["BTC"] == "negative"
    assert saved.sentiment_by_brand["Orange Botswana"] == "neutral"
    assert article.classification.id == saved.id
