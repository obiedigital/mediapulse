import pytest
from fastapi.testclient import TestClient

from mediapulse.api.deps import get_db
from mediapulse.api.main import app
from mediapulse.auth import hash_password
from mediapulse.models import User, UserRole


@pytest.fixture()
def client(session):
    def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(session, tenant, *, email, role=UserRole.analyst, password="test-password-123"):
    user = User(
        tenant_id=tenant.id if role != UserRole.platform_admin else None,
        email=email, name=email.split("@")[0], role=role,
        hashed_password=hash_password(password),
    )
    session.add(user)
    session.flush()
    return user


def login(client, email, password="test-password-123"):
    response = client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(client, session, tenant, *, role=UserRole.analyst, email="tester@example.bw"):
    make_user(session, tenant, email=email, role=role)
    token = login(client, email)
    return {"Authorization": f"Bearer {token}"}
