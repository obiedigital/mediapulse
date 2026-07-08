import datetime as dt
import json

from mediapulse.ai.client import MessageResult
from mediapulse.api.deps import get_ai_client
from mediapulse.api.main import app
from mediapulse.models import Article, Classification, ClassificationStatus, Topic, TopicKind

from .conftest import auth_headers


class FakeClient:
    def __init__(self, response):
        self._response = response

    def create_message(self, *, model, content, max_tokens=4096):
        return MessageResult(text=self._response, input_tokens=500, output_tokens=200)


def _seed_article(session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Botswana business & fintech", kind=TopicKind.sector)
    session.add(topic)
    session.flush()
    day = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    article = Article(tenant_id=tenant.id, topic_id=topic.id, publication="Mmegi Online",
                       title="Orange Money crosses one million active users", published_at=day, fetched_at=day,
                       content_hash="h1", raw_text="Orange Money reached one million active users this quarter.")
    session.add(article)
    session.flush()
    session.add(Classification(article_id=article.id, tenant_id=tenant.id, status=ClassificationStatus.success,
                                summary_exec="Orange Money growth milestone."))
    session.flush()
    return article


def test_ask_requires_auth(client):
    response = client.post("/ask", json={"question": "How is Orange Money doing?"})
    assert response.status_code == 401


def test_ask_returns_answer_with_citations(client, session, tenant):
    article = _seed_article(session, tenant)
    fake_response = json.dumps({
        "answer": "Orange Money reached one million users this quarter.",
        "citations": [{"article_id": article.id, "title": article.title}],
    })
    app.dependency_overrides[get_ai_client] = lambda: FakeClient(fake_response)
    try:
        headers = auth_headers(client, session, tenant)
        response = client.post("/ask", json={"question": "How is Orange Money doing?"}, headers=headers)
    finally:
        del app.dependency_overrides[get_ai_client]

    assert response.status_code == 200
    body = response.json()
    assert "Orange Money" in body["answer"]
    assert body["citations"][0]["article_id"] == article.id


def test_ask_returns_502_on_ai_failure(client, session, tenant, monkeypatch):
    monkeypatch.setattr("mediapulse.ai.ask.time.sleep", lambda seconds: None)
    _seed_article(session, tenant)
    app.dependency_overrides[get_ai_client] = lambda: FakeClient("not json")
    try:
        headers = auth_headers(client, session, tenant)
        response = client.post(
            "/ask", json={"question": "How is Orange Money doing?"},
            headers={**headers},
        )
    finally:
        del app.dependency_overrides[get_ai_client]

    # default ai_max_retries in settings could make this slow; keep expectation
    # focused on the failure surfacing as a clean 502, not a raw 500 traceback.
    assert response.status_code == 502
    assert "could not answer" in response.json()["detail"]
