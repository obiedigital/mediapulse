# Changelog

## M1 — Ingestion

RSS + PressReader workers, and the rebuilt PDF article-segmentation
pipeline, proven against two synthetic sample PDFs standing in for the
real Daily News (10-06-2026) and Botswana Gazette (06-05-2026) — no real
legacy PDFs, `mediapulse.db`, or `dashboard_data.json` exist in this repo
(see M0's "known gaps"), so `tests/fixtures/build_sample_pdfs.py` generates
representative two-column pages carrying the exact headlines named as
expected output in the product brief.

**Added**
- `ingestion/dedupe.py` — cross-outlet story clustering (`StoryCluster`,
  pickup counts) via rapidfuzz title similarity within a recency window;
  kept separate from the exact-duplicate `content_hash` guard each worker
  already does at insert time.
- `ingestion/base.py` — shared `IngestResult`, `compute_content_hash`, and
  uniform `Source` health tracking (`last_fetched_at`/`last_success_at`/
  `consecutive_error_count`/`last_error`) so every connector reports the
  same shape to the future admin source-health page.
- `ingestion/rss.py` — feedparser-based worker with an injectable fetch
  function (network call is a single seam, so tests never hit the
  network). Idempotent on rerun, records source-level errors on fetch/parse
  failure without needing a full stack trace to show up on the health page.
- `ingestion/pressreader.py` — connector interface (`PressReaderClient`
  protocol) for the same insert/dedupe/health path, since PressReader has
  no public content API and the legacy scraper isn't in this repo. Fails
  loudly and specifically ("client not configured") rather than crashing
  or silently no-op'ing; a real scraper implementation is a one-file
  addition once credentials exist.
- `ingestion/pdf.py` — layout-aware print segmentation: PyMuPDF block
  extraction, dynamic column clustering from x-coordinates, a heading
  font-size heuristic (checked after a non-editorial keyword check, so a
  bold "INVITATION TO TENDER" doesn't get mistaken for a headline),
  masthead date detection reusing the M0 date-repair checksum logic,
  "To Page N"/"From Page N" continuation merging across pages, and a
  `pages_needing_vision_fallback` signal when a page has no headline-sized
  text and no real body (a heavily degraded scan).
- `ai/vision_segment.py` — Claude-vision fallback for those flagged pages:
  renders the page to PNG, asks for the same structured shape the
  heuristic path produces, retries a configurable number of times on
  unparseable JSON rather than trusting or discarding garbage output
  (direct lesson from defect #1). The Anthropic client is injected, so this
  is fully unit-tested with zero network calls / no API key required.
- `ingestion/manual.py` — backend half of the "manual upload of PDFs/links
  through the UI" requirement, callable now via CLI ahead of the M3 UI:
  `ingest_pdf` runs the full segmentation + vision-fallback pipeline and
  inserts articles with the document's masthead date; `ingest_link`
  fetches and stores a single pasted URL.
- `mediapulse ingest` now actually runs every active RSS/PressReader
  source for a tenant (PDF sources are one-shot uploads, not polled).
  Added `mediapulse ingest-pdf` and `mediapulse ingest-link` for the manual
  path. All three verified end-to-end against a real SQLite DB, including
  the RSS worker's real (network-blocked) error path and the PressReader
  stub's "not configured" path.
- `tests/fixtures/build_sample_pdfs.py` — generates the two synthetic
  sample PDFs; regenerate with `python tests/fixtures/build_sample_pdfs.py`.
- 31 new tests (51 total): dedupe clustering, RSS worker (canned feed
  XML, idempotency, fetch/parse failure), PressReader worker (fake
  client), PDF segmentation against both synthetic PDFs (correct
  headlines/dates/continuation merge, ads and notices excluded from
  editorial output, vision-fallback flagging on a degraded page), vision
  segmentation (retry-on-bad-JSON, markdown-fence stripping, exhausted
  retries raise clearly), and manual PDF/link ingest.

**Known gaps going into M2**
- Still no real legacy corpus or real sample newspaper PDFs in this repo —
  if you have them, send them over so the pipeline can be validated
  against actual OCR/layout quirks rather than the synthetic fixtures.
- PressReader has no working scraper behind the connector interface yet —
  needs real credentials/session details before it can fetch anything.
- The heading font-size threshold (13pt) and non-editorial keyword list
  are heuristics tuned against the synthetic fixtures; expect to widen
  them once real papers are available.

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
