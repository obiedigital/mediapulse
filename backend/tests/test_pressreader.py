import datetime as dt

from mediapulse.ingestion import pressreader
from mediapulse.ingestion.pressreader import PressReaderArticle
from mediapulse.models import Article, Source, SourceType, Topic, TopicKind


class FakePressReaderClient:
    def __init__(self, articles):
        self._articles = articles

    def fetch_recent_articles(self, *, publication_id, since):
        return self._articles


def _make_source(session, tenant, *, publication_id="botswana-gazette"):
    topic = Topic(tenant_id=tenant.id, label="Botswana business & fintech", kind=TopicKind.sector)
    session.add(topic)
    session.flush()
    source = Source(
        topic_id=topic.id,
        name="Botswana Gazette",
        type=SourceType.pressreader,
        config={"publication_id": publication_id} if publication_id else {},
    )
    session.add(source)
    session.flush()
    return source


def test_pressreader_worker_inserts_articles_via_injected_client(session, tenant):
    source = _make_source(session, tenant)
    client = FakePressReaderClient([
        PressReaderArticle(
            title="Botswana bids for anti-money laundering academy",
            body="Government has submitted a bid to host the regional AML academy.",
            publication="Botswana Gazette",
            published_at=dt.datetime(2026, 5, 6, tzinfo=dt.timezone.utc),
            page_number=3,
        ),
    ])

    result = pressreader.run(session, source, client=client)

    assert result.inserted == 1
    assert result.errors == []
    article = session.query(Article).filter_by(tenant_id=tenant.id).one()
    assert article.title == "Botswana bids for anti-money laundering academy"
    assert article.page_number == 3
    assert source.last_success_at is not None


def test_pressreader_worker_fails_loudly_without_client(session, tenant):
    source = _make_source(session, tenant)

    result = pressreader.run(session, source, client=None)

    assert result.inserted == 0
    assert "not configured" in result.errors[0]
    assert source.consecutive_error_count == 1


def test_pressreader_worker_requires_publication_id(session, tenant):
    source = _make_source(session, tenant, publication_id=None)

    result = pressreader.run(session, source, client=FakePressReaderClient([]))

    assert result.errors == ["missing publication_id"]


def test_pressreader_worker_idempotent_on_rerun(session, tenant):
    source = _make_source(session, tenant)
    articles = [
        PressReaderArticle(
            title="Batanani Walk Targets Child Protection",
            body="Community members took part in a walk to raise child protection awareness.",
            publication="Daily News",
            published_at=dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc),
        ),
    ]
    client = FakePressReaderClient(articles)

    first = pressreader.run(session, source, client=client)
    second = pressreader.run(session, source, client=client)

    assert first.inserted == 1
    assert second.inserted == 0
    assert second.skipped_duplicates == 1
