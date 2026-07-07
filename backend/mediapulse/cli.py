from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Annotated, Optional

import typer

from .db import session_scope
from .models import Tenant, Topic, TopicKind

app = typer.Typer(help="MediaPulse BW operational CLI.")


def _require_tenant(session, slug: str) -> Tenant:
    tenant = session.query(Tenant).filter_by(slug=slug).one_or_none()
    if tenant is None:
        raise typer.BadParameter(
            f"No tenant with slug={slug!r}. Run `mediapulse seed-demo-tenant` or create one first."
        )
    return tenant


@app.command()
def init_db() -> None:
    """Create all tables directly from the models (dev convenience only —
    Alembic migrations are the source of truth for anything with real data)."""
    from .db import engine
    from .models import Base

    Base.metadata.create_all(engine)
    typer.echo("Tables created.")


@app.command()
def seed_demo_tenant() -> None:
    """Create the Orange Botswana tenant with its starter watchlist, matching
    the four topics named in the product brief."""
    with session_scope() as session:
        existing = session.query(Tenant).filter_by(slug="orange-bw").one_or_none()
        if existing is not None:
            typer.echo("Tenant 'orange-bw' already exists, skipping.")
            return

        tenant = Tenant(
            slug="orange-bw",
            name="Orange Botswana",
            brand_config={"primary": "#FF7900", "secondary": "#000000"},
        )
        session.add(tenant)
        session.flush()

        topics = [
            ("Orange Botswana (brand watch)", TopicKind.brand_watch,
             ["Orange Botswana", "Orange Money", "Orange Digital Center"]),
            ("Mascom & BTC (competitors)", TopicKind.competitor,
             ["Mascom", "BTC", "Botswana Telecommunications Corporation", "Smega", "MyZaka"]),
            ("BOCRA & regulation", TopicKind.regulator,
             ["BOCRA", "Botswana Communications Regulatory Authority"]),
            ("Botswana business & fintech", TopicKind.sector,
             ["fintech", "mobile money", "Botswana business"]),
        ]
        for label, kind, keywords in topics:
            session.add(Topic(tenant_id=tenant.id, label=label, kind=kind, keywords=keywords))

        typer.echo(f"Seeded tenant 'orange-bw' with {len(topics)} topics.")


@app.command()
def import_legacy(
    db_path: Annotated[Path, typer.Option(help="Path to legacy mediapulse.db (SQLite)")],
    tenant: Annotated[str, typer.Option(help="Tenant slug to attach imported articles to")],
    dashboard_json: Annotated[
        Optional[Path], typer.Option(help="Path to legacy dashboard_data.json, if available")
    ] = None,
    report_path: Annotated[
        Path, typer.Option(help="Where to write the date-repair report")
    ] = Path("legacy_import_report.json"),
) -> None:
    """Import the legacy SQLite `articles` table (+ optional dashboard_data.json),
    repairing publication dates and re-queuing classification for every row."""
    from .scripts.import_legacy import run_legacy_import

    with session_scope() as session:
        tenant_row = _require_tenant(session, tenant)
        report = run_legacy_import(
            session=session,
            tenant=tenant_row,
            legacy_db_path=db_path,
            dashboard_json_path=dashboard_json,
        )
    report.write(report_path)
    typer.echo(
        f"Imported {report.imported} articles ({report.dates_repaired} dates repaired, "
        f"{report.rejected_as_non_editorial} rejected as non-editorial, "
        f"{report.flagged_needs_review} flagged needs_review). "
        f"Full report: {report_path}"
    )


@app.command()
def ingest(
    tenant: Annotated[str, typer.Option(help="Tenant slug")],
    topic: Annotated[Optional[str], typer.Option(help="Limit to one topic label")] = None,
) -> None:
    """Run all active sources for a tenant (RSS/PressReader/PDF watch folder).

    M1 deliverable — ingestion workers land in `mediapulse.ingestion`; this
    stub already resolves the tenant/topic scope so workers just need to be
    plugged in behind it.
    """
    with session_scope() as session:
        _require_tenant(session, tenant)
    typer.echo(
        "Ingestion workers are not implemented yet (M1). "
        "Tenant/topic scoping is wired; see mediapulse/ingestion/."
    )
    raise typer.Exit(code=1)


@app.command()
def classify(
    tenant: Annotated[str, typer.Option(help="Tenant slug")],
    reprocess_errors: Annotated[
        bool, typer.Option(help="Re-run classification for articles in `error` status")
    ] = False,
) -> None:
    """Run AI enrichment over pending (or errored) articles for a tenant.

    M2 deliverable — see mediapulse/ai/.
    """
    with session_scope() as session:
        _require_tenant(session, tenant)
    typer.echo("AI classification pipeline is not implemented yet (M2). See mediapulse/ai/.")
    raise typer.Exit(code=1)


@app.command()
def brief(
    tenant: Annotated[str, typer.Option(help="Tenant slug")],
    date: Annotated[str, typer.Option(help="Reference date, or 'today'")] = "today",
    brief_type: Annotated[str, typer.Option(help="daily|weekly|monthly")] = "daily",
) -> None:
    """Generate (and optionally email) a brief for a tenant.

    M4 deliverable.
    """
    ref_date = dt.date.today() if date == "today" else dt.date.fromisoformat(date)
    with session_scope() as session:
        _require_tenant(session, tenant)
    typer.echo(
        f"Brief generation is not implemented yet (M4). "
        f"Would generate a {brief_type} brief for {ref_date.isoformat()}."
    )
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
