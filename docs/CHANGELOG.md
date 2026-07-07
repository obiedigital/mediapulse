# Changelog

## M0 — Scaffold

Repo layout, config, DB models/migrations, and legacy-data import script
with a date-repair report.

**Added**
- `backend/` Python package (Python 3.11+, FastAPI/SQLAlchemy dependencies
  declared for later milestones; nothing wired to a web server yet).
- `mediapulse/config.py` — single source of settings, no hardcoded model
  strings anywhere else in the codebase (this is what let the legacy
  pipeline 404 silently on `claude-sonnet-4-20250514`). Classification and
  brief-synthesis models are independently configurable.
- SQLAlchemy models: `Tenant`, `User` (with a `platform_admin` role that
  spans tenants), `Topic` (a tenant's watchlist entries), `Source`
  (per-topic feed with health tracking: last fetch/success, error streak),
  `Article` (tenant-denormalized, holds both `published_at` and
  `fetched_at` plus a `published_at_confidence`), `StoryCluster` (dedup
  groups with pickup counts), `Classification` (per-article AI output,
  `sentiment_by_brand` is a dict — sentiment is brand-directed, not
  article-wide), `Brief` (daily/weekly/monthly archive rows).
- Alembic migrations, verified upgrade/downgrade round-trip on SQLite.
- `mediapulse` CLI (Typer): `init-db`, `seed-demo-tenant` (creates the
  Orange Botswana tenant with its four starter topics), `import-legacy`,
  and stubs for `ingest`/`classify`/`brief` that resolve tenant scope and
  report which milestone implements them.
- `mediapulse/ingestion/dates.py` — recovers true publication dates from
  print masthead text (e.g. "Wednesday June 10, 2026 | No. 83",
  "WEDNESDAY 06 MAY 2026"), using the weekday name as a checksum against
  the parsed calendar date; rejects implausible years/future dates. This
  directly targets defect #2 (4,243 print items carrying the fetch date or
  garbage like `1780-46-43`).
- `mediapulse/scripts/import_legacy.py` — imports a legacy SQLite
  `articles` table into the new schema: discards the legacy
  `classification`/`classified_at` columns entirely and re-queues every row
  (defect #1 — those columns were produced by 404ing API calls), applies
  the date-repair logic above, flags <60-char bodies as `needs_review`
  (a first pass at defect #3 pending the real PDF re-segmentation in M1),
  and rejects obvious tenders/legal notices as non-editorial. Idempotent on
  rerun via `content_hash`. Writes a JSON repair report.
- 20 passing pytest cases covering config loading, date extraction/repair
  edge cases, tenant-scoped model relationships, and legacy import against
  a synthetic fixture DB (no real legacy `mediapulse.db` exists in this
  repo yet — tests build one on the fly).

**Known gaps going into M1**
- No real legacy `mediapulse.db`, `dashboard_data.json`, or sample
  newspaper PDFs are present in this repo. `import-legacy` and the M1 PDF
  pipeline both need real input files (or synthetic stand-ins) supplied
  before they can be exercised against actual Daily News / Botswana
  Gazette pages.
- Ingestion workers (RSS, PressReader, PDF), the AI enrichment module, the
  FastAPI app, and the React frontend do not exist yet — `mediapulse_platform.html`
  at the repo root is a static design reference only.
