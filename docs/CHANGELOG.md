# Changelog

## M3 — API + dashboard

FastAPI backend and a React dashboard, verified end-to-end in a real
browser against the real API (screenshots taken via Playwright/Chromium):
login → overview → story feed → story detail → share of voice → daily
brief archive → admin source health, across three roles (admin, analyst,
client-portal groundwork via `client_viewer`).

**Added — backend**
- `auth.py` — PBKDF2-SHA256 password hashing (stdlib only, no native
  extension) and JWT issuance/verification (`pyjwt`).
- `api/deps.py` — tenant-scoping dependency: a tenant-bound user always
  sees their own tenant's data (a `?tenant=` override to another tenant is
  rejected with 403); a `platform_admin` (no tenant_id) must pass
  `?tenant=<slug>` to select one. `require_roles()` gates admin-only routes.
- `schemas/` — Pydantic response models for every endpoint. `published_at`
  on `ArticleListItemOut`/`ArticleDetailOut` is never optional — the
  articles router resolves `published_at or fetched_at` before
  constructing the response, so a null date can't reach the frontend as
  "Invalid Date" (M0 defect #4, now fixed by construction, not convention).
- `api/routers/articles.py` — story feed with filters (date range,
  publication, sentiment, category, status, brand, free-text search),
  pagination, CSV export, and story detail.
- `api/routers/analytics.py` — KPIs, share-of-voice (brand mentions/day,
  carries an explicit "directional, not full-media-monitoring-universe"
  methodology note per the house style rule), sentiment trend by brand,
  topic mix, top publications, byline tracker.
- `api/routers/health.py` — public `/health`, admin-only `/admin/sources`
  (the source-health page backing data: last fetch/success, error streak).
- `api/routers/briefs.py` — read-only Daily Brief archive (empty until M4).
- `mediapulse create-user` CLI command; `mediapulse seed-demo-data` seeds
  realistic classified articles, sources (one healthy, one erroring), and
  three demo logins (admin/analyst/client_viewer) without needing a real
  Anthropic API key.
- Fixed a real cross-database bug surfaced while seeding: SQLite has no
  true timezone-aware storage, so a `StoryCluster` row re-fetched after
  its TimestampMixin server-default post-INSERT refresh came back with a
  naive `last_seen_at`, crashing `max(naive, aware)` in
  `ingestion/dedupe.py`. Fixed by normalizing to UTC-aware before
  comparing — affects SQLite dev/test only, Postgres round-trips
  correctly.
- 21 new API tests (98 total) covering auth, tenant isolation (a
  tenant-scoped user cannot read another tenant's data even by query-param
  override), filter correctness, KPI/SOV/sentiment-trend/topic-mix math
  against known fixtures, CSV export, and role-gated admin access.

**Added — frontend**
- React + Vite + TypeScript + Tailwind v4 + Recharts + react-router.
  Orange brand (`#FF7900`) for UI chrome (logo, active nav, buttons);
  chart/status colors use the dataviz skill's validated CVD-safe default
  palette instead of brand hues, with light/dark tokens both wired
  (`prefers-color-scheme` plus a `data-theme` override hook for a future
  manual toggle) — brand color and data color are deliberately different
  color systems here.
  Categorical hues (share-of-voice brand lines) are assigned in
  first-seen order per entity and never re-cycled; sentiment/threat
  badges pair a status color with an icon dot *and* a text label, never
  color alone.
- Pages: Login, Overview (KPI tiles + share-of-voice line chart + topic
  mix bar chart), Story Feed (filterable/paginated table + CSV export),
  Story Detail (summary, why-it-matters, per-brand sentiment, entities,
  key quotes, full text), Share of Voice (larger SOV + per-brand
  sentiment-trend stacked bars), Daily Brief archive (empty state), Admin
  (source health table, role-gated).
- Every state handles the "not yet classified" / "failed" article
  gracefully (a `null` classification renders "Pending analysis" and a
  visible error status, not a crash) — checked live against the seeded
  pending/error demo rows, not just the happy path.

**Known gaps going into M4**
- Brand/entity JSON filtering in the articles endpoint is done in Python
  after SQL-level filters run (documented in `articles.py`) — fine at
  current data volumes, worth moving to Postgres jsonb operators before a
  tenant's corpus grows much larger.
- No live Anthropic API run yet (same gap as M2) — dashboard has only
  been exercised against seeded/fixture classifications.
- Daily Brief generation itself (M4) still needs building; the archive
  UI/API are ready for it.

## M2 — AI enrichment

Classification, per-brand sentiment, entity extraction, summarisation, and
threat tagging, with the model config fix from M0 finally exercised
end-to-end: an article that comes in through `import-legacy` (re-queued,
legacy classification discarded) now flows cleanly through `mediapulse
classify` and comes out the other side with real intelligence.

**Added**
- `ai/client.py` — single shared Anthropic SDK adapter (`AnthropicClient`
  protocol + `AnthropicClientAdapter`) used by both classification and the
  M1 vision fallback, so there's exactly one place that reads a model
  string and records token usage. `ai/vision_segment.py` refactored onto
  this instead of its own copy.
- `ai/json_utils.py` — shared markdown-fence stripping for model JSON
  output, also deduplicated out of `vision_segment.py`.
- `ai/pricing.py` — per-tier (opus/sonnet/haiku) $/Mtok table for
  `cost_usd` logging on every `Classification` row; returns `None` for an
  unrecognized model rather than guessing a number.
- `ai/schemas.py` — strict Pydantic schema for the classification
  response (`relevance_score`, `category`, `sentiment_overall`,
  per-brand `sentiment_by_brand`, `entities`, `summary_exec`,
  `key_quotes`, `why_it_matters`, `threat_tag`, `threat_rationale`) that
  mirrors the `Classification` table field-for-field, so a response
  missing something fails validation instead of landing half-populated.
- `ai/prompts.py` — tenant-aware prompt builder: injects the tenant's full
  watchlist (brand-watch/competitor/regulator/sector topics with
  keywords) so the same pipeline judges sentiment, category, and
  threat/opportunity/monitor tagging from *that tenant's* point of view
  (a BTC price cut is a `risk` for Orange, sector news for a bank).
- `ai/classify.py` — `classify_article()` (retry/backoff on bad JSON,
  same discipline as the M1 vision fallback; exhausted retries mark
  `Classification.status=failed` + `Article.status=error` with the real
  error recorded, never silently) and `classify_pending()` (the batch
  runner behind the CLI, with an explicit `reprocess_errors` queue).
- `mediapulse classify --tenant --reprocess-errors --limit` now actually
  runs enrichment; verified end-to-end against a real SQLite DB (correctly
  reports and exits non-zero on an auth failure with no API key
  configured, rather than crashing).
- 18 new tests (69 total): shared client refactor (vision tests updated to
  the new protocol), pricing, prompt injection, schema validation
  (rejects out-of-range relevance, invalid sentiment enum), classify
  retry/failure/reclassification behavior, batch runner status filtering,
  and a full legacy-import → classify end-to-end test proving defect #1
  is fixed in practice, not just in isolated units.

**Known gaps going into M3**
- No real `ANTHROPIC_API_KEY` is configured in this environment, so
  classification has only been run against a fake client in tests/CLI
  smoke tests — worth one real run against the live API before trusting
  output quality/latency.
- `category` is a free string constrained only by prompt instruction, not
  a DB-level enum — worth revisiting once real classified data shows
  what categories actually show up.
- No API layer or React dashboard yet — `mediapulse brief` is still a
  stub.

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
