import datetime as dt
import json

import pytest

from mediapulse.ai.brief_synthesis import (
    BriefSynthesisError,
    build_brief_prompt,
    generate_brief_synthesis,
)
from mediapulse.ai.client import MessageResult
from mediapulse.briefs.aggregate import build_brief_data
from mediapulse.models import Article, Classification, ClassificationStatus, ThreatTag, Topic, TopicKind

VALID_PAYLOAD = {
    "exec_summary": "Coverage was broadly positive for Orange Botswana this week.",
    "pillar_commentary": {"Client": "Strong CSR and network stories.", "Competitors": "BTC pushed price competition."},
    "sentiment_commentary": "BTC sentiment moved from neutral to negative on the price cut story.",
    "watchlist_actions": {},
}


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create_message(self, *, model, content, max_tokens=4096):
        self.calls += 1
        response = self._responses[min(self.calls - 1, len(self._responses) - 1)]
        if isinstance(response, Exception):
            raise response
        return MessageResult(text=response, input_tokens=800, output_tokens=300)


def _make_data(session, tenant):
    client_topic = Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch)
    competitor_topic = Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor)
    session.add_all([client_topic, competitor_topic])
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    a1 = Article(tenant_id=tenant.id, topic_id=client_topic.id, publication="Mmegi", title="Orange story",
                 published_at=day, fetched_at=day, content_hash="h1", raw_text="body")
    session.add(a1)
    session.flush()
    session.add(Classification(article_id=a1.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                                category="csr", sentiment_by_brand={"Orange Botswana": "positive"},
                                threat_tag=ThreatTag.opportunity, threat_rationale="Good CSR story", relevance_score=0.9))

    a2 = Article(tenant_id=tenant.id, topic_id=competitor_topic.id, publication="The Voice", title="BTC price cut",
                 published_at=day, fetched_at=day, content_hash="h2", raw_text="body")
    session.add(a2)
    session.flush()
    session.add(Classification(article_id=a2.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                                category="telco", sentiment_by_brand={"BTC": "negative"},
                                threat_tag=ThreatTag.risk, threat_rationale="Price attack line", relevance_score=0.8))
    session.flush()

    return build_brief_data(session, tenant, period_start=dt.date(2026, 6, 10), period_end=dt.date(2026, 6, 10))


def test_prompt_includes_pillars_sov_and_watchlist(session, tenant):
    data = _make_data(session, tenant)
    prompt = build_brief_prompt(data)

    assert "Orange story" in prompt
    assert "BTC price cut" in prompt
    assert "Client" in prompt
    assert "Competitors" in prompt
    assert "Orange Digital Center" in prompt  # house style rule present in prompt
    assert "Price attack line" in prompt


def test_generate_brief_synthesis_parses_valid_response(session, tenant):
    data = _make_data(session, tenant)
    client = FakeClient([json.dumps(VALID_PAYLOAD)])

    result = generate_brief_synthesis(data, client=client, max_retries=3, backoff_seconds=0)

    assert result.exec_summary == VALID_PAYLOAD["exec_summary"]
    assert result.pillar_commentary["Client"] == "Strong CSR and network stories."
    assert client.calls == 1


def test_generate_brief_synthesis_retries_on_bad_json(session, tenant):
    data = _make_data(session, tenant)
    client = FakeClient(["not json", json.dumps(VALID_PAYLOAD)])

    result = generate_brief_synthesis(data, client=client, max_retries=3, backoff_seconds=0)

    assert client.calls == 2
    assert result.sentiment_commentary


def test_generate_brief_synthesis_raises_after_exhausting_retries(session, tenant):
    data = _make_data(session, tenant)
    client = FakeClient(["garbage", "garbage", "garbage"])

    with pytest.raises(BriefSynthesisError, match="failed after 3 attempts"):
        generate_brief_synthesis(data, client=client, max_retries=3, backoff_seconds=0)
