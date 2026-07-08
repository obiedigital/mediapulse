# Changelog

## Digital-native redesign — landing page, login, client portal

Replaces the static `mediapulse_platform.html` mockup with a real,
wired-up public entry point, and gives the client-facing surfaces a
distinct, consumer-grade look instead of the analyst dashboard's
utilitarian styling.

- **`frontend/src/marketing.css`** — a scoped dark theme (`.mp-marketing`)
  porting the mockup's ink/orange/teal, Syne+Inter brand system into
  reusable classes. Namespaced so it never leaks into the light-mode
  dataviz-token system the analyst dashboard uses.
- **`frontend/src/pages/Landing.tsx`** — the real public `/` route: hero,
  live-feeling signal cards, a metrics band, and a feature grid covering
  the platform's actual capabilities (AI classification, layout-aware
  PDF ingestion, Daily Brief, Ask MediaPulse, alerts, client portal).
  Redirects straight to `/dashboard` if you're already signed in.
- **`frontend/src/pages/Login.tsx`** — redesigned in the same dark brand
  language instead of the plain light-mode form.
- **`frontend/src/pages/ClientPortal.tsx`** — a distinct `client_viewer`
  home: a greeting, three plain-language highlight cards (opportunities /
  worth watching / risks), and a spotlight on the latest Daily Brief —
  no share-of-voice chart or topic-mix breakdown, consistent with the
  portal's "zero data-plumbing visible" intent that the nav gating
  already enforced but the old Overview page didn't honor.
- Routing: `Overview` moved from `/` to `/dashboard`; `/` is now the
  public landing page. `App.tsx` picks `ClientPortal` vs `Overview` at
  `/dashboard` based on role.
- Verified live via Playwright: landing → login → analyst dashboard →
  client portal, screenshotted at each step; 161 backend tests still
  pass unaffected (frontend-only change).

## SMTP implicit-TLS (port 465) support

While wiring a real client mail server (`mail.ebw.co.bw`, port 465) for
Daily Brief delivery, found that `notify/email.py` only supported
STARTTLS (port 587) — calling `.starttls()` on an already-encrypted
port-465 connection is wrong and most servers reject it. Added a
`smtp_use_ssl` config flag and a `_default_connection()` helper that
picks `smtplib.SMTP_SSL` vs `smtplib.SMTP` accordingly, with 4 new tests
covering both conventions. Live delivery itself remains unverified: this
sandbox's egress proxy only proxies HTTPS/443 traffic, and raw SMTP (TCP,
non-443) isn't supported through it — a hard environment limitation, not
a code or credentials issue.

## Live verification against the real Anthropic API

Ran `mediapulse classify` and `mediapulse brief` for real, against a
temporary API key provided for this one-off test (rotated by the owner
immediately after — never committed, logged, or written to any file).

- **Classification** (`claude-sonnet-4-6`): a real BTC-price-cut story
  classified in ~11s for $0.0088. Output correctly reasoned per-brand
  directional sentiment — `"BTC": "positive"` (good news for BTC),
  `"Orange Botswana": "negative"` (bad news for Orange) — from the same
  article, plus accurate entities, a tight two-sentence summary, and a
  specific `risk` threat rationale.
- **Daily Brief** (`claude-opus-4-8` synthesis): generated in ~12.6s.
  Real output: a sharp exec summary, pillar commentary that correctly
  caveated a 1-mention data point as "an early signal, not a trend,"
  and a watch-list recommended action specific enough to act on
  ("Convene a rapid pricing and retention review of prepaid data
  bundles... before the story gains traction").
- Found and fixed a real README bug while running this: the documented
  `mediapulse brief --type daily` flag doesn't exist — the actual option
  is `--brief-type`.

This closes the "no live API run" standing gap for the classification and
brief-synthesis paths specifically. SMTP delivery is still unverified
(no SMTP credentials were provided for this pass).

## Scheduler — unattended operation

Closes the "no scheduler wiring ingest → classify → brief → alerts
together automatically" gap. `mediapulse scheduler` is a long-lived
foreground process (its own container — see the `scheduler` service in
`docker-compose.yml`, separate from the API server) that runs the exact
same functions the CLI commands call, on a recurring schedule, for every
active tenant:

- ingest every `MEDIAPULSE_SCHEDULER_INGEST_INTERVAL_MINUTES` (default 30)
- classify every `MEDIAPULSE_SCHEDULER_CLASSIFY_INTERVAL_MINUTES` (default 15)
- alert digest + volume-spike check every
  `MEDIAPULSE_SCHEDULER_ALERTS_INTERVAL_MINUTES` (default 60)
- daily brief checked hourly, sent once a tenant's configured
  `daily_brief_hour_utc` matches the current UTC hour

**Added**
- `Tenant.notification_config` (new JSON column + migration) —
  `{"brief_recipients": [...], "alert_recipients": [...],
  "daily_brief_hour_utc": 6}`. A tenant with no recipients configured
  still gets ingested/classified/alert-evaluated by the scheduler; it
  just doesn't get anything emailed automatically. Set via the new
  `mediapulse set-notifications --tenant --brief-to --alert-to
  --daily-brief-hour-utc` command.
- `mediapulse/scheduler.py` — four cycle functions
  (`run_ingest_cycle`/`run_classify_cycle`/`run_alerts_cycle`/
  `run_daily_brief_job`), each a thin loop over active tenants calling
  the same underlying functions the CLI uses (no duplicated business
  logic), wrapped in `try/except` per-tenant so one tenant's failure
  doesn't take down the cycle for everyone else. `mediapulse scheduler`
  starts it (APScheduler `BlockingScheduler`); verified live that it
  starts, registers all four jobs, and successfully runs an immediate
  ingest cycle.
- `docker-compose.yml` gained a `scheduler` service (same image as
  `backend`, different command) and a shared `x-backend-env` YAML anchor
  so the two services' environment blocks can't drift out of sync.
- 8 new tests (158 total) covering the orchestration logic itself
  (tenant iteration, active/inactive filtering, recipient/hour gating)
  by monkeypatching the underlying work functions — those functions
  already have their own dedicated suites, so these tests only check the
  scheduler's wiring, not re-test ingestion/classification/brief logic.

**On the other standing gap — no live Anthropic API/SMTP run yet**: this
one isn't fixable by writing more code. It needs real credentials
(`ANTHROPIC_API_KEY`, and SMTP host/user/password if you want email
delivery verified too) that only the project owner has. The moment
those are available — as env vars for a live CLI/scheduler smoke test, or
in a deployed environment — the exact same code path runs for real;
nothing here is mocked in a way that would need changing. Recommended
first real-world check: `mediapulse classify --tenant orange-bw --limit 1`
against one seeded article, then `mediapulse brief --tenant orange-bw`,
both with a real `ANTHROPIC_API_KEY` set, before trusting output
quality/latency/cost at scale.

## M5 — Alerts, Ask MediaPulse, client portal, Docker

Rounds out the platform: near-real-time alerts, a RAG-style "Ask
MediaPulse" chat, a genuinely read-only client portal (not just a role
label), a real multi-tenant onboarding path, and containerization.

**Added — Alerts**
- `models/alert.py` — new `Alert` table + migration (`article_id`
  nullable for the day-scoped volume-spike type). Idempotent by design:
  article-scoped alerts are keyed on (article_id, alert_type); volume
  spikes on (tenant_id, alert_type, day).
- `alerts/rules.py` — three article-scoped rules fired automatically as a
  side effect of `ai/classify.py`'s successful classification (negative
  sentiment on the tenant's own brand-watch topic, a competitor-topic
  story matching launch keywords, any regulator-topic story), plus a
  day-scoped `evaluate_volume_spike` (today's count vs. a trailing
  7-day average, with an absolute floor so a barely-onboarded tenant
  doesn't get spurious spike alerts on day one).
- `notify/alerts.py` — one digest email per run rather than one email per
  alert; `notify/email.py` refactored to expose a generic `send_email`
  both the Brief (with PDF attachment) and the alert digest (without) call.
- `mediapulse alerts --tenant --send-to` (volume-spike check + digest
  delivery) and `GET /alerts` (tenant-scoped, newest first).

**Added — Ask MediaPulse**
- `ai/ask.py` — lexical retrieval (`search_articles`: query-term overlap
  scored against title/summary/body, weighted title > summary > body)
  over the tenant's corpus — the "Postgres full-text search to start"
  phase from the product brief; swapping in pgvector similarity later is
  isolated to this one function. `ask_mediapulse` asks the synthesis
  model to answer using only the retrieved articles, with citations, same
  retry-on-bad-JSON discipline as classification/brief synthesis, and an
  `AskError` on exhausted retries.
- `POST /ask` (tenant-scoped, 502 with a clear message on AI failure
  rather than a raw 500) and a new "Ask MediaPulse" dashboard page — a
  lightweight running Q&A history with citation chips linking to story
  detail. Verified live: an unanswerable question (no API key configured)
  surfaces the clean error text in the UI, not a crash.

**Added — client portal + multi-tenant onboarding**
- The `client_viewer` role is now genuinely restricted, not just RBAC'd
  on the backend: Story Feed, Share of Voice, and Ask MediaPulse are
  hidden from nav *and* route-guarded (a direct URL doesn't bypass it) —
  "zero data-plumbing visible" for the Client CMO persona, verified live
  with a screenshot showing the client login sees only Overview + Daily
  Brief.
- `mediapulse create-tenant` + `mediapulse add-topic` generalize
  `seed-demo-tenant` into a real onboarding path for any client (bank,
  mining house, government, telco) — the brief's multi-tenant requirement
  no longer only works for the Orange Botswana demo.

**Added — Docker**
- `backend/Dockerfile` (+ `docker-entrypoint.sh` running `alembic upgrade
  head` before serving), `frontend/Dockerfile` (multi-stage Vite build →
  nginx, `/api/` reverse-proxied to the backend service), and
  `docker-compose.yml` (Postgres + backend + frontend, named volumes for
  Postgres data and brief PDFs).
- **Caveat**: the Docker daemon is unavailable in this sandboxed dev
  environment (nested containers aren't permitted here), so `docker build`
  / `docker compose up` could not be executed end-to-end. Validated what
  was possible instead: `docker compose config` parses and resolves
  cleanly, and the WeasyPrint system-package list is confirmed correct
  since this same sandbox already runs WeasyPrint successfully on an
  equivalent Debian base. Worth a real `docker compose up` smoke test in
  an environment where Docker actually runs before calling this done.

**Added — tests**
- 30 new tests (150 total): alert rule detection (all four types,
  idempotency), alert digest email construction, Ask retrieval ranking
  and prompt construction, Ask retry/failure behavior, and API tests for
  both `/alerts` and `/ask` (tenant isolation, auth, clean 502 on AI
  failure via a `get_ai_client` FastAPI dependency override).

**Known gaps**
- No live Anthropic API or SMTP server exercised yet (same standing gap
  since M2 — everything verified against fakes/fixtures).
- Docker Compose stack unverified end-to-end (see caveat above).
- Alert rules are a fixed set, not tenant-configurable — no rule-builder
  UI. Volume-spike thresholds are also fixed constants, not per-tenant
  tunable.
- Ask MediaPulse retrieval is O(n) over the tenant's full article table
  in Python — fine at current scale, but the brief's own phased plan
  calls for embeddings/pgvector once corpus size actually warrants it.
- No scheduler (cron/APScheduler) wiring `classify`/`brief`/`alerts`
  together automatically — still manual CLI invocations.

## M4 — Daily Brief generator + email

The flagship deliverable: `mediapulse brief --tenant orange-bw --date today
--send-to client@orange.bw` generates a full agency-quality brief (exec
summary, four pillars, share of voice, sentiment shifts, a Risk/
Opportunity/Monitor watch list with recommended actions, methodology
footnote), renders it to email-safe HTML and a PDF, persists it to the
`Brief` archive (already exposed via the M3 API/UI), and optionally emails
it — verified end to end including a real rendered PDF checked visually,
not just asserted on byte count.

**Added**
- `briefs/aggregate.py` — pulls one tenant-period's classified coverage
  into pillars (Client/Competitors/Regulator/Sector, from each `Topic`'s
  kind), share of voice, sentiment shifts vs. the immediately preceding
  period of equal length, and a Risk/Opportunity watch list (risk items
  first, then by relevance). Deliberately has no AI dependency — pure
  arithmetic over already-classified rows, fully unit tested without a
  model client.
- `ai/brief_synthesis.py` — asks the `synthesis_model` (the stronger model
  reserved for this, per M0's config split) to write the exec summary,
  per-pillar commentary, sentiment-shift narrative, and a one-line
  recommended action per watch-list item, around the numbers `aggregate.py`
  already computed. Same retry discipline as classification/vision: bad
  JSON is retried, and a final failure raises `BriefSynthesisError`
  clearly instead of shipping a broken brief. Prompt embeds the house
  style rule (always "Orange Digital Center", US spelling) and instructs
  the model not to invent facts.
- `briefs/render.py` — Jinja2 template (flexbox rows, not nested tables —
  a WeasyPrint quirk left "Orange Botswana7" glued together with no gap
  under `table-layout:fixed`, caught by actually rendering and looking at
  the PDF, not just asserting substrings) to email-safe HTML, plus a
  WeasyPrint PDF export. Brand color reads from `tenant.brand_config`, so
  the same template serves any tenant. Threat-tag colors match the
  frontend's dataviz status palette so Risk/Opportunity/Monitor reads the
  same in the emailed brief as on the dashboard.
- `notify/email.py` — stdlib-only SMTP delivery (HTML body + PDF
  attachment), SMTP connection injectable for testing, a `notify/` package
  (not a one-off function) so WhatsApp/Slack alerting can land the same way.
- `briefs/generate.py` — orchestrates aggregate → synthesize → render →
  upsert `Brief` row (rerunning the same tenant/type/period updates it in
  place rather than duplicating).
- `mediapulse brief --tenant --date --type --send-to` fully wired: caught
  a real UX gap in testing — a synthesis failure was surfacing as a raw
  Typer traceback instead of the clean "Xxx failed: <reason>, exit 1"
  pattern the other commands use; fixed by giving brief synthesis its own
  exception type (`BriefSynthesisError`) and catching it in the CLI.
- 26 new tests (123 total): pillar grouping/ranking, share-of-voice and
  sentiment-shift math against known fixtures, watch-list ordering,
  prompt content, synthesis retry/failure, HTML section rendering (brand
  color, empty watch list, brief-type label correctness — daily vs.
  weekly), a real PDF written to disk and checked for the `%PDF` magic
  bytes, and SMTP message construction (TLS/login/attachment) against an
  injected fake connection.

**Known gaps going into M5**
- No live Anthropic API run yet (same gap as M2/M3).
- No live SMTP server exercised — email sending is verified against a
  fake connection object, not a real inbox.
- Brief generation isn't scheduled (no cron/APScheduler wiring yet) —
  it's a manual CLI invocation. Automating "every morning" is M5/ops work.
- Demo seed data (`seed_demo_data.py`) cycles through only 7 story
  templates over 14 days, so a 7-day weekly-brief window can show the
  same headline twice — cosmetic, fixture-only, not a product defect.

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
