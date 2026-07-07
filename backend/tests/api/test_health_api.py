from mediapulse.models import Source, SourceType, Topic, TopicKind, UserRole

from .conftest import auth_headers


def test_health_is_public():
    from fastapi.testclient import TestClient

    from mediapulse.api.main import app

    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_sources_requires_admin_role(client, session, tenant):
    headers = auth_headers(client, session, tenant, role=UserRole.analyst)
    response = client.get("/admin/sources", headers=headers)
    assert response.status_code == 403


def test_admin_sources_visible_to_admin(client, session, tenant):
    topic = Topic(tenant_id=tenant.id, label="Orange watch", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    session.add(Source(
        topic_id=topic.id, name="Mmegi Online", type=SourceType.rss,
        url="https://mmegi.bw/feed", consecutive_error_count=2, last_error="timeout",
    ))
    session.flush()

    headers = auth_headers(client, session, tenant, role=UserRole.admin, email="admin@orange.bw")
    response = client.get("/admin/sources", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body[0]["name"] == "Mmegi Online"
    assert body[0]["consecutive_error_count"] == 2
    assert body[0]["last_error"] == "timeout"
