"""Background scheduler wiring ingest -> classify -> alerts -> brief
together automatically, per tenant, so the platform runs unattended
instead of needing someone to invoke each `mediapulse ...` command by
hand. This is the "Orchestrate with a simple scheduler" piece the
architecture called for from day one.

Each cycle function is a thin loop over active tenants calling the exact
same underlying functions the CLI commands call — no duplicated business
logic, just cadence. Runs in the foreground (`mediapulse scheduler`),
intended to be its own long-lived process/container (see
docker-compose.yml's `scheduler` service), separate from the API server.

Delivery is opt-in per tenant via `Tenant.notification_config`
(`brief_recipients`, `alert_recipients`, `daily_brief_hour_utc`) — a
tenant with no recipients configured still gets ingested/classified/
alert-evaluated, it just doesn't get anything emailed automatically.
"""
from __future__ import annotations

import datetime as dt
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session

from .ai.classify import classify_pending
from .alerts.rules import evaluate_volume_spike
from .briefs.generate import generate_brief
from .config import get_settings
from .db import session_scope
from .ingestion import pressreader, rss
from .models import Alert, BriefStatus, BriefType, Source, SourceType, Tenant, Topic
from .notify.alerts import send_alert_digest
from .notify.email import send_brief_email

logger = logging.getLogger("mediapulse.scheduler")


def _active_tenants(session: Session) -> list[Tenant]:
    return session.query(Tenant).filter_by(is_active=True).all()


def run_ingest_cycle() -> None:
    """Poll every active RSS/PressReader source for every active tenant."""
    with session_scope() as session:
        for tenant in _active_tenants(session):
            sources = (
                session.query(Source)
                .join(Topic)
                .filter(Topic.tenant_id == tenant.id, Source.is_active.is_(True))
                .all()
            )
            for source in sources:
                try:
                    if source.type == SourceType.rss:
                        result = rss.run(session, source)
                    elif source.type == SourceType.pressreader:
                        result = pressreader.run(session, source)
                    else:
                        continue
                    logger.info(
                        "ingest tenant=%s source=%s inserted=%s errors=%s",
                        tenant.slug, source.name, result.inserted, len(result.errors),
                    )
                except Exception:
                    logger.exception("ingest failed tenant=%s source=%s", tenant.slug, source.name)


def run_classify_cycle() -> None:
    """Classify pending articles for every active tenant."""
    with session_scope() as session:
        for tenant in _active_tenants(session):
            try:
                result = classify_pending(session, tenant=tenant)
                if result.processed:
                    logger.info(
                        "classify tenant=%s processed=%s succeeded=%s failed=%s",
                        tenant.slug, result.processed, result.succeeded, result.failed,
                    )
            except Exception:
                logger.exception("classify failed tenant=%s", tenant.slug)


def run_alerts_cycle() -> None:
    """Check for a coverage-volume spike, then email a digest of any
    unsent alerts — only for tenants with `alert_recipients` configured."""
    with session_scope() as session:
        for tenant in _active_tenants(session):
            try:
                evaluate_volume_spike(session, tenant)
                recipients = (tenant.notification_config or {}).get("alert_recipients") or []
                if not recipients:
                    continue
                pending = session.query(Alert).filter_by(tenant_id=tenant.id, sent_at=None).all()
                if not pending:
                    continue
                for to in recipients:
                    send_alert_digest(tenant_name=tenant.name, alerts=pending, to=to)
                now = dt.datetime.now(dt.timezone.utc)
                for alert in pending:
                    alert.sent_at = now
                logger.info(
                    "alerts tenant=%s sent=%s recipients=%s", tenant.slug, len(pending), len(recipients)
                )
            except Exception:
                logger.exception("alerts failed tenant=%s", tenant.slug)


def run_daily_brief_job() -> None:
    """Generate + email the daily brief for tenants with `brief_recipients`
    configured, once their `daily_brief_hour_utc` matches the current UTC
    hour. Scheduled hourly (see `start_scheduler`) so an hour match is
    checked, not a specific minute — safe to run more than once an hour
    since a same-day brief regenerates in place rather than duplicating."""
    now = dt.datetime.now(dt.timezone.utc)
    with session_scope() as session:
        for tenant in _active_tenants(session):
            config = tenant.notification_config or {}
            recipients = config.get("brief_recipients") or []
            send_hour = config.get("daily_brief_hour_utc", 6)
            if not recipients or now.hour != send_hour:
                continue
            try:
                brief = generate_brief(
                    session, tenant=tenant, brief_type=BriefType.daily, reference_date=now.date(),
                )
                for to in recipients:
                    send_brief_email(
                        to=to,
                        subject=f"{tenant.name} Daily Brief — {now.date().isoformat()}",
                        html_body=brief.html_content,
                        pdf_path=brief.pdf_path,
                    )
                brief.sent_at = now
                brief.status = BriefStatus.sent
                logger.info("brief tenant=%s recipients=%s", tenant.slug, len(recipients))
            except Exception:
                logger.exception("brief generation/send failed tenant=%s", tenant.slug)


def start_scheduler() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    settings = get_settings()
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_ingest_cycle, "interval", minutes=settings.scheduler_ingest_interval_minutes,
        id="ingest", next_run_time=dt.datetime.now(),
    )
    scheduler.add_job(
        run_classify_cycle, "interval", minutes=settings.scheduler_classify_interval_minutes,
        id="classify",
    )
    scheduler.add_job(
        run_alerts_cycle, "interval", minutes=settings.scheduler_alerts_interval_minutes,
        id="alerts",
    )
    scheduler.add_job(run_daily_brief_job, "cron", minute=0, id="daily_brief")

    logger.info(
        "MediaPulse scheduler starting (ingest every %sm, classify every %sm, "
        "alerts every %sm, brief check hourly)...",
        settings.scheduler_ingest_interval_minutes,
        settings.scheduler_classify_interval_minutes,
        settings.scheduler_alerts_interval_minutes,
    )
    scheduler.start()
