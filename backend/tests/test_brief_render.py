import datetime as dt

from mediapulse.ai.brief_synthesis import BriefSynthesisResult
from mediapulse.briefs.aggregate import build_brief_data
from mediapulse.briefs.render import render_brief_html, render_brief_pdf
from mediapulse.models import Article, BriefType, Classification, ClassificationStatus, ThreatTag, Topic, TopicKind


def _make_data(session, tenant, brief_type=BriefType.daily):
    client_topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(client_topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    a1 = Article(tenant_id=tenant.id, topic_id=client_topic.id, publication="Mmegi", title="Orange Digital Center hosts bootcamp",
                 published_at=day, fetched_at=day, content_hash="h1", raw_text="body")
    session.add(a1)
    session.flush()
    session.add(Classification(article_id=a1.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                                category="csr", sentiment_by_brand={"Orange Botswana": "positive"},
                                threat_tag=ThreatTag.opportunity, threat_rationale="Good CSR story", relevance_score=0.9))
    session.flush()

    return build_brief_data(
        session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10),
        brief_type=brief_type,
    )


def _synthesis():
    return BriefSynthesisResult(
        exec_summary="A strong week for Orange Botswana with a standout CSR story.",
        pillar_commentary={"Client": "The bootcamp story reinforces the brand's tech-skills positioning."},
        sentiment_commentary="Sentiment remained positive across the period.",
        watchlist_actions={},
    )


def test_render_brief_html_includes_key_sections(session, tenant):
    data = _make_data(session, tenant)
    html = render_brief_html(data, _synthesis())

    assert "Orange Botswana" in html
    assert "Executive Summary" in html
    assert "A strong week for Orange Botswana" in html
    assert "Orange Digital Center hosts bootcamp" in html
    assert "Share of Voice" in html
    assert "OPPORTUNITY" in html
    assert "directional" in html  # methodology note present


def test_render_brief_html_labels_brief_type_correctly(session, tenant):
    daily_html = render_brief_html(_make_data(session, tenant, BriefType.daily), _synthesis())
    assert "Daily Brief" in daily_html
    assert "Weekly Media Brief" not in daily_html


def test_render_brief_html_labels_weekly_brief_correctly(session, tenant):
    weekly_data = _make_data(session, tenant, BriefType.weekly)
    weekly_html = render_brief_html(weekly_data, _synthesis())
    assert "Weekly Media Brief" in weekly_html
    assert "Daily Media Brief" not in weekly_html


def test_render_brief_html_uses_tenant_brand_color(session, tenant):
    tenant.brand_config = {"primary": "#123456"}
    data = _make_data(session, tenant)
    html = render_brief_html(data, _synthesis())
    assert "#123456" in html


def test_render_brief_html_handles_empty_watchlist(session, tenant):
    tenant2_data = _make_data(session, tenant)
    tenant2_data.watchlist = []
    html = render_brief_html(tenant2_data, _synthesis())
    assert "No risk or opportunity items flagged" in html


def test_render_brief_pdf_produces_valid_pdf_file(session, tenant, tmp_path):
    data = _make_data(session, tenant)
    html = render_brief_html(data, _synthesis())
    pdf_path = tmp_path / "brief.pdf"

    render_brief_pdf(html, str(pdf_path))

    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert pdf_path.stat().st_size > 500
