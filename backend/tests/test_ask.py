import datetime as dt
import json

import pytest

from mediapulse.ai.ask import AskError, ask_mediapulse, build_ask_prompt, search_articles
from mediapulse.ai.client import MessageResult
from mediapulse.models import Article, Classification, ClassificationStatus, Topic, TopicKind

VALID_RESPONSE = json.dumps({
    "answer": "Orange Money grew faster than Smega this quarter based on the retrieved coverage.",
    "citations": [{"article_id": "will-be-replaced", "title": "Orange Money crosses one million active users"}],
})


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create_message(self, *, model, content, max_tokens=4096):
        self.calls += 1
        response = self._responses[min(self.calls - 1, len(self._responses) - 1)]
        return MessageResult(text=response, input_tokens=600, output_tokens=250)


def _seed_corpus(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Botswana business & fintech", kind=TopicKind.sector)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)

    a1 = Article(tenant_id=tenant.id, topic_id=topic.id, publication="Mmegi Online",
                 title="Orange Money crosses one million active users", published_at=day, fetched_at=day,
                 content_hash="h1", raw_text="Orange Money reached one million active mobile money users this quarter.")
    session.add(a1)
    session.flush()
    session.add(Classification(article_id=a1.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                                summary_exec="Orange Money mobile money growth milestone."))

    a2 = Article(tenant_id=tenant.id, topic_id=topic.id, publication="The Voice",
                 title="Smega expands merchant network", published_at=day, fetched_at=day,
                 content_hash="h2", raw_text="Smega added new merchant partners in Francistown this quarter.")
    session.add(a2)
    session.flush()
    session.add(Classification(article_id=a2.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                                summary_exec="Smega merchant network expansion."))

    a3 = Article(tenant_id=tenant.id, topic_id=topic.id, publication="Daily News",
                 title="BOCRA issues new spectrum licenses", published_at=day, fetched_at=day,
                 content_hash="h3", raw_text="The regulator issued new spectrum licenses to telecom operators.")
    session.add(a3)
    session.flush()

    session.flush()
    return a1, a2, a3


def test_search_articles_ranks_relevant_articles_first(session, tenant):
    a1, a2, a3 = _seed_corpus(session, tenant)

    results = search_articles(session, tenant, "How is Orange Money mobile money growth doing?")

    assert results[0].id == a1.id
    assert a3.id not in [r.id for r in results]  # spectrum licensing story is irrelevant


def test_search_articles_returns_empty_for_stopword_only_query(session, tenant):
    _seed_corpus(session, tenant)
    assert search_articles(session, tenant, "the of and") == []


def test_build_ask_prompt_includes_articles_and_question(session, tenant):
    a1, a2, a3 = _seed_corpus(session, tenant)
    prompt = build_ask_prompt(tenant=tenant, question="How did Orange Money compare to Smega?", articles=[a1, a2])

    assert "Orange Money crosses one million active users" in prompt
    assert "Smega expands merchant network" in prompt
    assert "How did Orange Money compare to Smega?" in prompt
    assert a1.id in prompt


def test_build_ask_prompt_handles_no_matching_articles(tenant):
    prompt = build_ask_prompt(tenant=tenant, question="Anything about drones?", articles=[])
    assert "no matching articles" in prompt


def test_ask_mediapulse_returns_answer_with_citations(session, tenant):
    a1, a2, a3 = _seed_corpus(session, tenant)
    response = json.dumps({
        "answer": "Orange Money grew to one million users this quarter.",
        "citations": [{"article_id": a1.id, "title": a1.title}],
    })
    client = FakeClient([response])

    result = ask_mediapulse(session, tenant, "How is Orange Money doing?", client=client, max_retries=1, backoff_seconds=0)

    assert "Orange Money" in result.answer
    assert result.citations[0].article_id == a1.id


def test_ask_mediapulse_retries_on_bad_json(session, tenant):
    _seed_corpus(session, tenant)
    client = FakeClient(["not json", VALID_RESPONSE])

    result = ask_mediapulse(session, tenant, "How is Orange Money doing?", client=client, max_retries=3, backoff_seconds=0)

    assert client.calls == 2
    assert result.answer


def test_ask_mediapulse_raises_after_exhausting_retries(session, tenant):
    _seed_corpus(session, tenant)
    client = FakeClient(["garbage", "garbage", "garbage"])

    with pytest.raises(AskError, match="failed after 3 attempts"):
        ask_mediapulse(session, tenant, "How is Orange Money doing?", client=client, max_retries=3, backoff_seconds=0)
