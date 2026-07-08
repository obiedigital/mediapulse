import datetime as dt

from mediapulse.models import Alert, AlertType

from .conftest import auth_headers


def test_alerts_list_requires_auth(client):
    response = client.get("/alerts")
    assert response.status_code == 401


def test_alerts_list_returns_tenant_scoped_alerts(client, session, tenant):
    session.add(Alert(tenant_id=tenant.id, alert_type=AlertType.negative_sentiment, message="Bad story."))
    session.flush()

    headers = auth_headers(client, session, tenant)
    response = client.get("/alerts", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["alert_type"] == "negative_sentiment"
    assert body[0]["message"] == "Bad story."


def test_alerts_list_ordered_newest_first(client, session, tenant):
    a1 = Alert(tenant_id=tenant.id, alert_type=AlertType.regulator_announcement, message="First",
               created_at=dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc))
    session.add(a1)
    session.flush()
    a2 = Alert(tenant_id=tenant.id, alert_type=AlertType.volume_spike, message="Second",
               created_at=dt.datetime(2026, 6, 2, tzinfo=dt.timezone.utc))
    session.add(a2)
    session.flush()

    headers = auth_headers(client, session, tenant)
    response = client.get("/alerts", headers=headers)

    messages = [a["message"] for a in response.json()]
    assert messages[0] == "Second"
