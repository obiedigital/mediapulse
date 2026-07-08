import datetime as dt
import json

from mediapulse.ai.client import MessageResult
from mediapulse.briefs.generate import generate_brief, resolve_period
from mediapulse.models import (
    Article,
    Brief,
    BriefStatus,
    BriefType,
    Classification,
    ClassificationStatus,
    ThreatTag,
    Topic,
    TopicKind,
)

VALID_RESPONSE = json.dumps({
    "exec_summary": "A quiet but positive period for Orange Botswana.",
    "pillar_commentary": {"Client": "Steady positive coverage."},
    "sentiment_commentary": "No major shifts detected.",
    "watchlist_actions": {},
})


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create_message(self, *, model, content, max_tokens=4096):
        self.calls += 1
        response = self._responses[min(self.calls - 1, len(self._responses) - 1)]
        return MessageResult(text=response, input_tokens=500, output_tokens=200)


def _seed_article(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    article = Article(tenant_id=tenant.id, topic_id=topic.id, publication="Mmegi", title="Orange story",
                       published_at=day, fetched_at=day, content_hash="h1", raw_text="body")
    session.add(article)
    session.flush()
    session.add(Classification(article_id=article.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                                category="csr", sentiment_by_brand={"Orange Botswana": "positive"},
                                threat_tag=ThreatTag.opportunity, threat_rationale="Good story", relevance_score=0.9))
    session.flush()


def test_resolve_period_daily():
    ref = dt.date(2026, 6, 10)
    assert resolve_period(BriefType.daily, ref) == (ref, ref)


def test_resolve_period_weekly():
    ref = dt.date(2026, 6, 10)
    start, end = resolve_period(BriefType.weekly, ref)
    assert (end - start).days == 6
    assert end == ref


def test_generate_brief_creates_and_persists_row(session, tenant, tmp_path):
    _seed_article(session, tenant)
    client = FakeClient([VALID_RESPONSE])

    brief = generate_brief(
        session, tenant=tenant, brief_type=BriefType.daily,
        reference_date=dt.date(2026, 6, 10), client=client, storage_dir=tmp_path,
    )

    assert brief.status == BriefStatus.published
    assert brief.html_content is not None
    assert "Orange story" in brief.html_content
    assert brief.pdf_path is not None
    assert (tmp_path / f"{tenant.slug}-daily-2026-06-10.pdf").exists()
    assert brief.model_used

    rows = session.query(Brief).filter_by(tenant_id=tenant.id).all()
    assert len(rows) == 1


def test_generate_brief_rerun_updates_existing_row_not_duplicate(session, tenant, tmp_path):
    _seed_article(session, tenant)
    client = FakeClient([VALID_RESPONSE, VALID_RESPONSE])

    first = generate_brief(
        session, tenant=tenant, brief_type=BriefType.daily,
        reference_date=dt.date(2026, 6, 10), client=client, storage_dir=tmp_path,
    )
    second = generate_brief(
        session, tenant=tenant, brief_type=BriefType.daily,
        reference_date=dt.date(2026, 6, 10), client=client, storage_dir=tmp_path,
    )

    assert first.id == second.id
    assert session.query(Brief).filter_by(tenant_id=tenant.id).count() == 1
