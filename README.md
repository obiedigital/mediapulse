# MediaPulse BW

AI-powered media intelligence platform for the PR/communications industry in
Botswana (DS Communications). Multi-tenant: the flagship tenant is Orange
Botswana, but any client (banks, mining, government, telcos) gets its own
watchlist, competitors, and topics.

See the delivery plan and full product brief in the original kickoff prompt;
this repo tracks it milestone by milestone in `docs/CHANGELOG.md`.

## Status

**M0 (scaffold) is done.** Ingestion workers, AI enrichment, the API, and the
React dashboard are not built yet — `mediapulse ingest`/`classify`/`brief`
are wired-up stubs that resolve tenant/topic scope and then tell you which
milestone implements them.

`mediapulse_platform.html` at the repo root is a static design reference for
the eventual React frontend (landing page + app-shell mockup) — it is not
served by the backend.

## Layout

```
backend/
  mediapulse/
    config.py        # all env-driven settings; nothing else reads os.environ
    db.py             # SQLAlchemy engine/session
    models/           # Tenant, User, Topic, Source, Article, StoryCluster,
                       # Classification, Brief — all tenant-scoped
    cli.py            # `mediapulse ...` entrypoint (Typer)
    ingestion/         # RSS/PressReader/PDF workers land here (M1);
                       # dates.py (masthead date recovery) already lives here
    ai/                 # Anthropic SDK wrapper lands here (M2)
    scripts/
      import_legacy.py # legacy SQLite -> new schema, with date repair
  migrations/          # Alembic
  tests/
docs/
  CHANGELOG.md
```

## Local dev setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp ../.env.example ../.env   # fill in ANTHROPIC_API_KEY etc.

alembic upgrade head
python -m mediapulse.cli seed-demo-tenant
python -m pytest
```

## Importing the legacy Colab-era corpus

If you have the legacy `mediapulse.db` (and optionally `dashboard_data.json`):

```bash
python -m mediapulse.cli import-legacy \
  --db-path /path/to/mediapulse.db \
  --dashboard-json /path/to/dashboard_data.json \
  --tenant orange-bw \
  --report-path legacy_import_report.json
```

This repairs the two known legacy defects on the way in:

- **Dead classification pipeline**: legacy `classification`/`classified_at`
  columns are discarded, not ported — every row is re-queued (`status=new`)
  for enrichment under the current model config (see `.env.example`).
- **Garbage/fetch-date publication dates**: `mediapulse/ingestion/dates.py`
  re-derives the true publication date from the masthead text (with a
  weekday-name checksum) instead of trusting the legacy column, and records
  a confidence level (`high`/`medium`/`low`) plus the matched raw text on
  each `Article` row.

It does **not** re-segment OCR fragments (defect #3) — that needs the
rebuilt PDF pipeline working from the original PDFs (M1). For now it flags
obvious fragments (<60-char bodies) and non-editorial content (tenders,
legal notices) as `needs_review` / `rejected` so they stop being counted as
coverage.
