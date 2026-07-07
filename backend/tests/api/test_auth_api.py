from mediapulse.models import UserRole

from .conftest import login, make_user


def test_login_success_returns_token_and_profile(client, session, tenant):
    make_user(session, tenant, email="analyst@orange.bw", role=UserRole.analyst)

    response = client.post(
        "/auth/login", data={"username": "analyst@orange.bw", "password": "test-password-123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "analyst"
    assert body["tenant_id"] == tenant.id
    assert body["access_token"]


def test_login_rejects_wrong_password(client, session, tenant):
    make_user(session, tenant, email="analyst@orange.bw")

    response = client.post(
        "/auth/login", data={"username": "analyst@orange.bw", "password": "wrong"}
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email(client, session, tenant):
    response = client.post(
        "/auth/login", data={"username": "nobody@orange.bw", "password": "whatever"}
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, session, tenant):
    make_user(session, tenant, email="analyst@orange.bw", role=UserRole.analyst)
    token = login(client, "analyst@orange.bw")

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "analyst@orange.bw"


def test_me_rejects_tampered_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
