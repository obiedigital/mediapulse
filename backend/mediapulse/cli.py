from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Annotated, Optional

import typer

from .db import session_scope
from .models import Source, SourceType, Tenant, Topic, TopicKind, User, UserRole

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
def create_user(
    email: Annotated[str, typer.Option(help="Login email")],
    password: Annotated[str, typer.Option(prompt=True, hide_input=True, confirmation_prompt=True)],
    name: Annotated[str, typer.Option(help="Display name")],
    role: Annotated[str, typer.Option(help="platform_admin|admin|analyst|client_viewer")] = "analyst",
    tenant: Annotated[
        Optional[str], typer.Option(help="Tenant slug (omit for platform_admin)")
    ] = None,
) -> None:
    """Create a login for the API/dashboard."""
    from .auth import hash_password

    try:
        role_enum = UserRole(role)
    except ValueError as exc:
        raise typer.BadParameter(f"role must be one of {[r.value for r in UserRole]}") from exc

    with session_scope() as session:
        tenant_id = None
        if role_enum != UserRole.platform_admin:
            if not tenant:
                raise typer.BadParameter("--tenant is required unless --role=platform_admin")
            tenant_id = _require_tenant(session, tenant).id
        elif tenant:
            raise typer.BadParameter("--tenant must be omitted for --role=platform_admin")

        if session.query(User).filter_by(email=email).first():
            raise typer.BadParameter(f"A user with email {email!r} already exists.")

        session.add(User(
            tenant_id=tenant_id, email=email, name=name, role=role_enum,
            hashed_password=hash_password(password),
        ))
    typer.echo(f"Created user {email!r} ({role}).")


@app.command()
def seed_demo_data(
    tenant: Annotated[str, typer.Option(help="Tenant slug")] = "orange-bw",
) -> None:
    """Seed realistic classified demo articles, sources, and login users for
    a tenant — dev/demo fixture data only, does not call the Anthropic API."""
    from .scripts.seed_demo_data import DEMO_PASSWORD, DEMO_USERS, seed_demo_data as run_seed

    with session_scope() as session:
        tenant_row = _require_tenant(session, tenant)
        run_seed(session, tenant_row)

    typer.echo(f"Seeded demo articles/sources/users for tenant {tenant!r}.")
    typer.echo(f"Demo logins (password: {DEMO_PASSWORD}):")
    for email, role, _ in DEMO_USERS:
        typer.echo(f"  {email} ({role.value})")


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
    """Run every active RSS/PressReader source for a tenant.

    PDF sources aren't polled here — they're one-shot uploads via
    `mediapulse ingest-pdf` (or the M3 UI equivalent) since a print PDF
    doesn't arrive on a schedule the same way a feed does.
    """
    from .ingestion import pressreader, rss

    with session_scope() as session:
        tenant_row = _require_tenant(session, tenant)
        query = (
            session.query(Source)
            .join(Topic)
            .filter(Topic.tenant_id == tenant_row.id, Source.is_active.is_(True))
        )
        if topic:
            query = query.filter(Topic.label == topic)
        sources = query.all()

        if not sources:
            typer.echo(f"No active sources found for tenant={tenant!r}" + (f", topic={topic!r}" if topic else ""))
            raise typer.Exit(code=1)

        totals = {"fetched": 0, "inserted": 0, "skipped_duplicates": 0, "errors": 0}
        for source in sources:
            if source.type == SourceType.rss:
                result = rss.run(session, source)
            elif source.type == SourceType.pressreader:
                result = pressreader.run(session, source)
            else:
                typer.echo(f"Skipping {source.name!r}: type {source.type.value} has no polling worker.")
                continue

            typer.echo(
                f"{source.name}: fetched={result.fetched} inserted={result.inserted} "
                f"skipped={result.skipped_duplicates} errors={len(result.errors)}"
            )
            for error in result.errors:
                typer.echo(f"  ! {error}")
            totals["fetched"] += result.fetched
            totals["inserted"] += result.inserted
            totals["skipped_duplicates"] += result.skipped_duplicates
            totals["errors"] += len(result.errors)

    typer.echo(
        f"Done. fetched={totals['fetched']} inserted={totals['inserted']} "
        f"skipped={totals['skipped_duplicates']} errors={totals['errors']}"
    )


@app.command()
def ingest_pdf(
    tenant: Annotated[str, typer.Option(help="Tenant slug")],
    topic: Annotated[str, typer.Option(help="Topic label to attach articles to")],
    pdf_path: Annotated[Path, typer.Option(help="Path to the newspaper PDF")],
    publication: Annotated[str, typer.Option(help="Outlet name, e.g. 'Daily News'")],
    no_vision_fallback: Annotated[
        bool, typer.Option(help="Skip the Claude-vision fallback for unresolved pages")
    ] = False,
) -> None:
    """Manually ingest one print PDF (Daily News, Botswana Gazette, ...)."""
    from .ingestion.manual import ingest_pdf as run_ingest_pdf

    with session_scope() as session:
        tenant_row = _require_tenant(session, tenant)
        topic_row = session.query(Topic).filter_by(tenant_id=tenant_row.id, label=topic).one_or_none()
        if topic_row is None:
            raise typer.BadParameter(f"No topic {topic!r} for tenant {tenant!r}.")

        result = run_ingest_pdf(
            session,
            tenant=tenant_row,
            topic=topic_row,
            pdf_path=pdf_path,
            publication=publication,
            use_vision_fallback=not no_vision_fallback,
        )

    typer.echo(
        f"Segmented {result.fetched} items: inserted={result.inserted} "
        f"skipped={result.skipped_duplicates} rejected_non_editorial={result.rejected_non_editorial}"
    )
    for error in result.errors:
        typer.echo(f"  ! {error}")


@app.command()
def ingest_link(
    tenant: Annotated[str, typer.Option(help="Tenant slug")],
    topic: Annotated[str, typer.Option(help="Topic label to attach the article to")],
    url: Annotated[str, typer.Option(help="URL to fetch and ingest")],
) -> None:
    """Manually ingest a single link pasted through the UI."""
    from .ingestion.manual import ingest_link as run_ingest_link

    with session_scope() as session:
        tenant_row = _require_tenant(session, tenant)
        topic_row = session.query(Topic).filter_by(tenant_id=tenant_row.id, label=topic).one_or_none()
        if topic_row is None:
            raise typer.BadParameter(f"No topic {topic!r} for tenant {tenant!r}.")

        result = run_ingest_link(session, tenant=tenant_row, topic=topic_row, url=url)

    if result.inserted:
        typer.echo(f"Ingested {url}")
    elif result.skipped_duplicates:
        typer.echo("Already ingested (duplicate).")
    else:
        typer.echo(f"Failed: {result.errors}")
        raise typer.Exit(code=1)


@app.command()
def classify(
    tenant: Annotated[str, typer.Option(help="Tenant slug")],
    reprocess_errors: Annotated[
        bool, typer.Option(help="Re-run classification for articles in `error` status")
    ] = False,
    limit: Annotated[
        Optional[int], typer.Option(help="Max number of articles to process this run")
    ] = None,
) -> None:
    """Run AI enrichment (relevance, sentiment-by-brand, entities, summary,
    threat tag) over pending (or errored) articles for a tenant."""
    from .ai.classify import classify_pending

    with session_scope() as session:
        tenant_row = _require_tenant(session, tenant)
        result = classify_pending(
            session, tenant=tenant_row, reprocess_errors=reprocess_errors, limit=limit
        )

    typer.echo(
        f"Processed {result.processed}: succeeded={result.succeeded} failed={result.failed} "
        f"est_cost=${result.total_cost_usd:.4f}"
    )
    for failure in result.failures:
        typer.echo(f"  ! {failure}")
    if result.failed:
        raise typer.Exit(code=1)


@app.command()
def brief(
    tenant: Annotated[str, typer.Option(help="Tenant slug")],
    date: Annotated[str, typer.Option(help="Reference date, or 'today'")] = "today",
    brief_type: Annotated[str, typer.Option(help="daily|weekly|monthly")] = "daily",
    send_to: Annotated[
        Optional[str], typer.Option(help="Email address to send the brief to")
    ] = None,
) -> None:
    """Generate (and optionally email) a brief for a tenant."""
    from .ai.brief_synthesis import BriefSynthesisError
    from .briefs.generate import generate_brief
    from .models import BriefStatus, BriefType
    from .notify.email import EmailNotConfigured, send_brief_email

    ref_date = dt.date.today() if date == "today" else dt.date.fromisoformat(date)
    try:
        brief_type_enum = BriefType(brief_type)
    except ValueError as exc:
        raise typer.BadParameter(f"brief_type must be one of {[t.value for t in BriefType]}") from exc

    with session_scope() as session:
        tenant_row = _require_tenant(session, tenant)
        try:
            brief_row = generate_brief(
                session, tenant=tenant_row, brief_type=brief_type_enum, reference_date=ref_date,
            )
        except BriefSynthesisError as exc:
            typer.echo(f"Brief generation failed: {exc}")
            raise typer.Exit(code=1) from exc
        typer.echo(
            f"Generated {brief_type} brief for {tenant!r}, period "
            f"{brief_row.period_start.date()}–{brief_row.period_end.date()}. PDF: {brief_row.pdf_path}"
        )

        if send_to:
            try:
                send_brief_email(
                    to=send_to,
                    subject=f"{tenant_row.name} {brief_type.title()} Brief — {ref_date.isoformat()}",
                    html_body=brief_row.html_content,
                    pdf_path=brief_row.pdf_path,
                )
                brief_row.sent_at = dt.datetime.now(dt.timezone.utc)
                brief_row.status = BriefStatus.sent
                typer.echo(f"Emailed brief to {send_to}.")
            except EmailNotConfigured as exc:
                typer.echo(f"Not sent — {exc}")
                raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
