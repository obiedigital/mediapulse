from mediapulse.ingestion import rss
from mediapulse.models import Article, ArticleStatus, Source, SourceType, Topic, TopicKind

SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Mmegi Online</title>
  <item>
    <title>Orange Botswana expands 4G coverage to Ghanzi</title>
    <link>https://mmegi.bw/orange-4g-ghanzi</link>
    <description>Orange Botswana has switched on new 4G towers in Ghanzi district.</description>
    <pubDate>Wed, 10 Jun 2026 08:00:00 GMT</pubDate>
  </item>
  <item>
    <title>BOCRA fines operator over service outage</title>
    <link>https://mmegi.bw/bocra-fine</link>
    <description>The regulator has fined a mobile operator for a week-long outage.</description>
    <pubDate>Wed, 10 Jun 2026 09:00:00 GMT</pubDate>
  </item>
</channel>
</rss>
"""

BROKEN_FEED = b"this is not xml at all {{{"


def _make_source(session, tenant, *, url="https://mmegi.bw/feed"):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    source = Source(topic_id=topic.id, name="Mmegi Online", type=SourceType.rss, url=url)
    session.add(source)
    session.flush()
    return source


def test_rss_worker_inserts_new_articles(session, tenant):
    source = _make_source(session, tenant)

    result = rss.run(session, source, fetcher=lambda url: SAMPLE_FEED.encode())

    assert result.fetched == 2
    assert result.inserted == 2
    assert result.errors == []
    articles = session.query(Article).filter_by(tenant_id=tenant.id).all()
    assert {a.title for a in articles} == {
        "Orange Botswana expands 4G coverage to Ghanzi",
        "BOCRA fines operator over service outage",
    }
    assert all(a.status == ArticleStatus.new for a in articles)
    assert all(a.published_at.year == 2026 for a in articles)
    assert source.last_success_at is not None
    assert source.consecutive_error_count == 0


def test_rss_worker_is_idempotent_on_rerun(session, tenant):
    source = _make_source(session, tenant)

    def fetcher(url):
        return SAMPLE_FEED.encode()

    first = rss.run(session, source, fetcher=fetcher)
    second = rss.run(session, source, fetcher=fetcher)

    assert first.inserted == 2
    assert second.inserted == 0
    assert second.skipped_duplicates == 2
    assert session.query(Article).filter_by(tenant_id=tenant.id).count() == 2


def test_rss_worker_records_source_error_on_fetch_failure(session, tenant):
    source = _make_source(session, tenant)

    def failing_fetcher(url):
        raise ConnectionError("DNS resolution failed")

    result = rss.run(session, source, fetcher=failing_fetcher)

    assert result.inserted == 0
    assert "DNS resolution failed" in result.errors[0]
    assert source.consecutive_error_count == 1
    assert "DNS resolution failed" in source.last_error


def test_rss_worker_handles_unparseable_feed(session, tenant):
    source = _make_source(session, tenant)

    result = rss.run(session, source, fetcher=lambda url: BROKEN_FEED)

    assert result.inserted == 0
    assert source.consecutive_error_count == 1


def test_rss_worker_requires_url(session, tenant):
    source = _make_source(session, tenant, url=None)

    result = rss.run(session, source)

    assert result.errors == ["missing url"]
    assert source.consecutive_error_count == 1
