import datetime as dt
import json

from mediapulse.ai.classify import classify_article, classify_pending
from mediapulse.ai.client import MessageResult
from mediapulse.models import (
    Alert,
    AlertType,
    Article,
    ArticleStatus,
    Classification,
    ClassificationStatus,
    Topic,
    TopicKind,
)

VALID_PAYLOAD = {
    "relevance_score": 0.85,
    "category": "telco",
    "sentiment_overall": "neutral",
    "sentiment_by_brand": {"Orange Botswana": "neutral", "BTC": "negative"},
    "entities": {"brands": ["Orange Botswana", "BTC"], "people": [], "organisations": [],
                 "products": [], "events": [], "locations": ["Gaborone"]},
    "summary_exec": "BTC cut prices; Orange held steady. Analysts see a competitive response coming.",
    "key_quotes": ["\"We remain focused on value\", said an Orange spokesperson."],
    "why_it_matters": "A competitor price cut increases pressure on Orange's data pricing strategy.",
    "threat_tag": "risk",
    "threat_rationale": "BTC undercutting on price could shift price-sensitive customers.",
}
VALID_RESPONSE = json.dumps(VALID_PAYLOAD)


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create_message(self, *, model, content, max_tokens=4096):
        self.calls += 1
        response = self._responses[min(self.calls - 1, len(self._responses) - 1)]
        if isinstance(response, Exception):
            raise response
        return MessageResult(text=response, input_tokens=500, output_tokens=200)


def _make_article(session, tenant, topic, *, status=ArticleStatus.new):
    now = dt.datetime.now(dt.timezone.utc)
    article = Article(
        tenant_id=tenant.id,
        topic_id=topic.id,
        publication="Mmegi Online",
        title="BTC cuts data prices",
        published_at=now,
        fetched_at=now,
        content_hash=f"hash-{id(object())}",
        raw_text="BTC announced a 20% cut in data bundle prices today in Gaborone.",
        status=status,
    )
    session.add(article)
    session.flush()
    return article


def _make_topic(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor,
                   keywords=["Mascom", "BTC"])
    session.add(topic)
    session.flush()
    return topic


def test_classify_article_success_persists_full_classification(session, tenant):
    topic = _make_topic(session, tenant)
    article = _make_article(session, tenant, topic)
    client = FakeClient([VALID_RESPONSE])

    classification = classify_article(
        session, article, tenant=tenant, topics=[topic], client=client, max_retries=3, backoff_seconds=0
    )

    assert classification.status == ClassificationStatus.success
    assert classification.sentiment_by_brand["BTC"] == "negative"
    assert classification.sentiment_by_brand["Orange Botswana"] == "neutral"
    assert classification.category == "telco"
    assert classification.threat_tag.value == "risk"
    assert classification.tokens_in == 500
    assert classification.tokens_out == 200
    assert classification.cost_usd is not None
    assert classification.model_used == "claude-sonnet-4-6"
    assert article.status == ArticleStatus.classified


def test_classify_article_triggers_negative_sentiment_alert_on_client_topic(session, tenant):
    client_topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(client_topic)
    session.flush()
    article = _make_article(session, tenant, client_topic)
    client = FakeClient([VALID_RESPONSE])  # sentiment_by_brand includes BTC: negative

    classify_article(session, article, tenant=tenant, topics=[client_topic], client=client, max_retries=1, backoff_seconds=0)

    alerts = session.query(Alert).filter_by(article_id=article.id).all()
    assert any(a.alert_type == AlertType.negative_sentiment for a in alerts)


def test_classify_article_retries_on_bad_json_then_succeeds(session, tenant):
    topic = _make_topic(session, tenant)
    article = _make_article(session, tenant, topic)
    client = FakeClient(["not json", VALID_RESPONSE])

    classification = classify_article(
        session, article, tenant=tenant, topics=[topic], client=client, max_retries=3, backoff_seconds=0
    )

    assert client.calls == 2
    assert classification.status == ClassificationStatus.success
    assert classification.attempt_count == 2


def test_classify_article_marks_error_after_exhausting_retries(session, tenant):
    topic = _make_topic(session, tenant)
    article = _make_article(session, tenant, topic)
    client = FakeClient(["garbage", "still garbage", "more garbage"])

    classification = classify_article(
        session, article, tenant=tenant, topics=[topic], client=client, max_retries=3, backoff_seconds=0
    )

    assert classification.status == ClassificationStatus.failed
    assert classification.error_message is not None
    assert article.status == ArticleStatus.error
    assert classification.attempt_count == 3


def test_classify_article_reclassification_updates_existing_row_not_duplicate(session, tenant):
    topic = _make_topic(session, tenant)
    article = _make_article(session, tenant, topic, status=ArticleStatus.error)
    client = FakeClient([VALID_RESPONSE])

    classify_article(session, article, tenant=tenant, topics=[topic], client=client, max_retries=1, backoff_seconds=0)
    classify_article(session, article, tenant=tenant, topics=[topic], client=client, max_retries=1, backoff_seconds=0)

    rows = session.query(Classification).filter_by(article_id=article.id).all()
    assert len(rows) == 1
    assert rows[0].status == ClassificationStatus.success


def test_classify_pending_processes_only_new_by_default(session, tenant):
    topic = _make_topic(session, tenant)
    new_article = _make_article(session, tenant, topic, status=ArticleStatus.new)
    error_article = _make_article(session, tenant, topic, status=ArticleStatus.error)
    client = FakeClient([VALID_RESPONSE])

    result = classify_pending(session, tenant=tenant, client=client, backoff_seconds=0)

    assert result.processed == 1
    assert new_article.status == ArticleStatus.classified
    assert error_article.status == ArticleStatus.error  # untouched


def test_classify_pending_reprocess_errors_includes_error_articles(session, tenant):
    topic = _make_topic(session, tenant)
    _make_article(session, tenant, topic, status=ArticleStatus.new)
    _make_article(session, tenant, topic, status=ArticleStatus.error)
    client = FakeClient([VALID_RESPONSE])

    result = classify_pending(session, tenant=tenant, reprocess_errors=True, client=client, backoff_seconds=0)

    assert result.processed == 2
    assert result.succeeded == 2


def test_classify_pending_tracks_failures_and_cost(session, tenant):
    topic = _make_topic(session, tenant)
    _make_article(session, tenant, topic)
    client = FakeClient(["garbage", "garbage", "garbage", "garbage", "garbage"])

    result = classify_pending(session, tenant=tenant, client=client, backoff_seconds=0)

    assert result.processed == 1
    assert result.failed == 1
    assert len(result.failures) == 1
    assert result.total_cost_usd >= 0
