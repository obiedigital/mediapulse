"""Tests the scheduler's orchestration logic (tenant iteration, active/
inactive filtering, recipient/hour gating) by monkeypatching the
underlying work functions — those functions (rss.run, classify_pending,
generate_brief, ...) already have their own dedicated test suites."""
import datetime as dt

import pytest

from mediapulse import scheduler as scheduler_module
from mediapulse.ai.classify import ClassifyBatchResult
from mediapulse.ingestion.base import IngestResult
from mediapulse.models import (
    Alert,
    AlertType,
    Brief,
    BriefStatus,
    BriefType,
    Source,
    SourceType,
    Tenant,
    Topic,
    TopicKind,
)


@pytest.fixture()
def other_tenant(session):
    t = Tenant(slug="other-bank", name="Other Bank", is_active=True)
    session.add(t)
    session.flush()
    return t


def test_run_ingest_cycle_calls_rss_and_pressreader_for_active_sources(session, tenant, monkeypatch):
    topic = Topic(tenant_id=tenant.id, label="Orange watch", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    session.add(Source(topic_id=topic.id, name="Feed A", type=SourceType.rss, url="https://x", is_active=True))
    session.add(Source(topic_id=topic.id, name="PR A", type=SourceType.pressreader, is_active=True))
    session.add(Source(topic_id=topic.id, name="Inactive", type=SourceType.rss, url="https://y", is_active=False))
    session.flush()

    calls = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(scheduler_module.rss, "run", lambda s, src: calls.append(("rss", src.name)) or IngestResult())
    monkeypatch.setattr(
        scheduler_module.pressreader, "run", lambda s, src: calls.append(("pressreader", src.name)) or IngestResult()
    )

    scheduler_module.run_ingest_cycle()

    assert ("rss", "Feed A") in calls
    assert ("pressreader", "PR A") in calls
    assert not any(name == "Inactive" for _, name in calls)


def test_run_ingest_cycle_skips_inactive_tenants(session, tenant, other_tenant, monkeypatch):
    tenant.is_active = False
    topic = Topic(tenant_id=other_tenant.id, label="Other watch", kind=TopicKind.brand_watch)
    session.add(topic)
    session.flush()
    session.add(Source(topic_id=topic.id, name="Feed B", type=SourceType.rss, url="https://z", is_active=True))
    session.flush()

    calls = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(scheduler_module.rss, "run", lambda s, src: calls.append(src.name) or IngestResult())

    scheduler_module.run_ingest_cycle()

    assert calls == ["Feed B"]


def test_run_classify_cycle_processes_every_active_tenant(session, tenant, other_tenant, monkeypatch):
    calls = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(
        scheduler_module, "classify_pending",
        lambda s, tenant, **kw: calls.append(tenant.slug) or ClassifyBatchResult(),
    )

    scheduler_module.run_classify_cycle()

    assert set(calls) == {tenant.slug, other_tenant.slug}


def test_run_alerts_cycle_skips_tenants_without_recipients(session, tenant, monkeypatch):
    session.add(Alert(tenant_id=tenant.id, alert_type=AlertType.regulator_announcement, message="News"))
    session.flush()

    sent = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(scheduler_module, "evaluate_volume_spike", lambda s, t: None)
    monkeypatch.setattr(scheduler_module, "send_alert_digest", lambda **kw: sent.append(kw))

    scheduler_module.run_alerts_cycle()

    assert sent == []
    assert session.query(Alert).filter_by(tenant_id=tenant.id).one().sent_at is None


def test_run_alerts_cycle_sends_digest_when_recipients_configured(session, tenant, monkeypatch):
    tenant.notification_config = {"alert_recipients": ["admin@orange.bw"]}
    session.add(Alert(tenant_id=tenant.id, alert_type=AlertType.regulator_announcement, message="News"))
    session.flush()

    sent = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(scheduler_module, "evaluate_volume_spike", lambda s, t: None)
    monkeypatch.setattr(scheduler_module, "send_alert_digest", lambda **kw: sent.append(kw))

    scheduler_module.run_alerts_cycle()

    assert len(sent) == 1
    assert sent[0]["to"] == "admin@orange.bw"
    alert = session.query(Alert).filter_by(tenant_id=tenant.id).one()
    assert alert.sent_at is not None


def test_run_daily_brief_job_skips_tenant_without_recipients(session, tenant, monkeypatch):
    generated = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(scheduler_module, "generate_brief", lambda **kw: generated.append(kw))

    scheduler_module.run_daily_brief_job()

    assert generated == []


def test_run_daily_brief_job_skips_tenant_when_hour_does_not_match(session, tenant, monkeypatch):
    off_hour = (dt.datetime.now(dt.timezone.utc).hour + 5) % 24
    tenant.notification_config = {"brief_recipients": ["client@orange.bw"], "daily_brief_hour_utc": off_hour}

    generated = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(scheduler_module, "generate_brief", lambda **kw: generated.append(kw))

    scheduler_module.run_daily_brief_job()

    assert generated == []


def test_run_daily_brief_job_generates_and_sends_when_hour_matches(session, tenant, monkeypatch):
    current_hour = dt.datetime.now(dt.timezone.utc).hour
    tenant.notification_config = {"brief_recipients": ["client@orange.bw"], "daily_brief_hour_utc": current_hour}
    session.flush()

    fake_brief = Brief(
        tenant_id=tenant.id, brief_type=BriefType.daily, status=BriefStatus.published,
        period_start=dt.datetime.now(dt.timezone.utc), period_end=dt.datetime.now(dt.timezone.utc),
        html_content="<p>brief</p>", pdf_path=None,
    )
    session.add(fake_brief)
    session.flush()

    sent = []
    monkeypatch.setattr(scheduler_module, "session_scope", _session_scope_stub(session))
    monkeypatch.setattr(scheduler_module, "generate_brief", lambda *a, **kw: fake_brief)
    monkeypatch.setattr(scheduler_module, "send_brief_email", lambda **kw: sent.append(kw))

    scheduler_module.run_daily_brief_job()

    assert len(sent) == 1
    assert sent[0]["to"] == "client@orange.bw"
    assert fake_brief.status == BriefStatus.sent
    assert fake_brief.sent_at is not None


def _session_scope_stub(session):
    from contextlib import contextmanager

    @contextmanager
    def _stub():
        yield session

    return _stub
