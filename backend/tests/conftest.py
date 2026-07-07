from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from mediapulse.models import Base, Tenant


@pytest.fixture()
def session():
    # FastAPI's TestClient runs sync path operations in a worker thread, so
    # API tests that reuse this fixture as the DB session need the
    # in-memory SQLite connection to survive across threads.
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as sess:
        yield sess


@pytest.fixture()
def tenant(session) -> Tenant:
    t = Tenant(slug="orange-bw", name="Orange Botswana")
    session.add(t)
    session.flush()
    return t
