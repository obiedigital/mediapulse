"""End-to-end Daily/Weekly/Monthly Brief generation: aggregate the period's
data, ask the synthesis model to write the prose, render HTML+PDF, and
upsert the `Brief` archive row (one row per tenant/type/period — rerunning
the same period updates it in place rather than duplicating).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from sqlalchemy.orm import Session

from ..ai.brief_synthesis import generate_brief_synthesis
from ..config import get_settings
from ..models import Brief, BriefStatus, BriefType, Tenant
from .aggregate import build_brief_data
from .render import render_brief_html, render_brief_pdf


def resolve_period(brief_type: BriefType, reference_date: dt.date) -> tuple[dt.date, dt.date]:
    if brief_type == BriefType.daily:
        return reference_date, reference_date
    if brief_type == BriefType.weekly:
        return reference_date - dt.timedelta(days=6), reference_date
    if brief_type == BriefType.monthly:
        return reference_date - dt.timedelta(days=29), reference_date
    raise ValueError(f"Unknown brief_type {brief_type!r}")


def generate_brief(
    session: Session,
    *,
    tenant: Tenant,
    brief_type: BriefType = BriefType.daily,
    reference_date: dt.date | None = None,
    client=None,
    storage_dir: str | Path | None = None,
) -> Brief:
    reference_date = reference_date or dt.date.today()
    period_start, period_end = resolve_period(brief_type, reference_date)

    data = build_brief_data(
        session, tenant, period_start=period_start, period_end=period_end, brief_type=brief_type,
    )
    synthesis = generate_brief_synthesis(data, client=client)
    html = render_brief_html(data, synthesis)

    settings = get_settings()
    output_dir = Path(storage_dir or settings.brief_storage_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{tenant.slug}-{brief_type.value}-{period_end.isoformat()}.pdf"
    render_brief_pdf(html, str(pdf_path))

    period_start_dt = dt.datetime.combine(period_start, dt.time.min, tzinfo=dt.timezone.utc)
    period_end_dt = dt.datetime.combine(period_end, dt.time.max, tzinfo=dt.timezone.utc)

    brief = (
        session.query(Brief)
        .filter_by(
            tenant_id=tenant.id, brief_type=brief_type,
            period_start=period_start_dt, period_end=period_end_dt,
        )
        .one_or_none()
    )
    if brief is None:
        brief = Brief(
            tenant_id=tenant.id, brief_type=brief_type,
            period_start=period_start_dt, period_end=period_end_dt,
        )
        session.add(brief)

    now = dt.datetime.now(dt.timezone.utc)
    brief.model_used = settings.synthesis_model
    brief.html_content = html
    brief.pdf_path = str(pdf_path)
    brief.generated_at = now
    brief.published_at = brief.published_at or now
    brief.status = BriefStatus.published
    session.flush()
    return brief
