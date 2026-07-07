from pathlib import Path

from mediapulse.ingestion.manual import ingest_link, ingest_pdf
from mediapulse.models import Article, ArticleStatus, Topic, TopicKind

FIXTURES = Path(__file__).parent / "fixtures"


def _make_topic(session, tenant, label="Orange Botswana (brand watch)"):
    topic = Topic(tenant_id=tenant.id, label=label, kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    return topic


def test_ingest_pdf_inserts_segmented_articles_with_masthead_date(session, tenant):
    topic = _make_topic(session, tenant)

    result = ingest_pdf(
        session,
        tenant=tenant,
        topic=topic,
        pdf_path=FIXTURES / "daily_news_2026-06-10.pdf",
        publication="Daily News",
    )

    assert result.inserted >= 3
    articles = session.query(Article).filter_by(tenant_id=tenant.id).all()
    titles = {a.title for a in articles}
    assert "Media Raises Freedom Concerns" in titles
    assert "Batanani Walk Targets Child Protection" in titles

    real_story = next(a for a in articles if a.title == "Media Raises Freedom Concerns")
    assert real_story.published_at.date().isoformat() == "2026-06-10"
    assert real_story.published_at_confidence == "high"
    assert real_story.status == ArticleStatus.new

    ad = next(a for a in articles if a.is_advert)
    assert ad.status == ArticleStatus.rejected


def test_ingest_pdf_is_idempotent_on_rerun(session, tenant):
    topic = _make_topic(session, tenant)

    first = ingest_pdf(
        session, tenant=tenant, topic=topic,
        pdf_path=FIXTURES / "gazette_2026-05-06.pdf", publication="Botswana Gazette",
    )
    second = ingest_pdf(
        session, tenant=tenant, topic=topic,
        pdf_path=FIXTURES / "gazette_2026-05-06.pdf", publication="Botswana Gazette",
    )

    assert first.inserted > 0
    assert second.inserted == 0
    assert second.skipped_duplicates == first.inserted


def test_ingest_link_extracts_title_and_body(session, tenant):
    topic = _make_topic(session, tenant)
    html = b"""<html><head><title>Orange Botswana launches 5G pilot</title></head>
    <body><p>Orange Botswana has begun a 5G pilot in Gaborone.</p></body></html>"""

    result = ingest_link(
        session, tenant=tenant, topic=topic, url="https://example.bw/5g-pilot",
        fetcher=lambda url: html,
    )

    assert result.inserted == 1
    article = session.query(Article).filter_by(tenant_id=tenant.id).one()
    assert article.title == "Orange Botswana launches 5G pilot"
    assert "5G pilot in Gaborone" in article.raw_text


def test_ingest_link_records_fetch_error(session, tenant):
    topic = _make_topic(session, tenant)

    def failing_fetcher(url):
        raise TimeoutError("upstream timed out")

    result = ingest_link(
        session, tenant=tenant, topic=topic, url="https://example.bw/broken",
        fetcher=failing_fetcher,
    )

    assert result.inserted == 0
    assert "upstream timed out" in result.errors[0]


def test_ingest_link_idempotent_on_rerun(session, tenant):
    topic = _make_topic(session, tenant)
    html = b"<html><head><title>Story</title></head><body><p>Body text here.</p></body></html>"

    def fetcher(url):
        return html

    first = ingest_link(session, tenant=tenant, topic=topic, url="https://example.bw/x", fetcher=fetcher)
    second = ingest_link(session, tenant=tenant, topic=topic, url="https://example.bw/x", fetcher=fetcher)

    assert first.inserted == 1
    assert second.inserted == 0
    assert second.skipped_duplicates == 1
