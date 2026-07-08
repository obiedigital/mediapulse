# MediaPulse BW

AI-powered media intelligence platform for the PR/communications industry in
Botswana (DS Communications). Multi-tenant: the flagship tenant is Orange
Botswana, but any client (banks, mining, government, telcos) gets its own
watchlist, competitors, and topics.

See the delivery plan and full product brief in the original kickoff prompt;
this repo tracks it milestone by milestone in `docs/CHANGELOG.md`.

## Status

**M0 (scaffold) through M4 (Daily Brief + email) are done.** RSS/
PressReader ingestion, a layout-aware print PDF pipeline, tenant-aware AI
classification, a FastAPI backend, a React dashboard, and the Daily/
Weekly/Monthly Brief generator (exec summary, pillars, share of voice,
sentiment shifts, Risk/Opportunity watch list, HTML+PDF, email delivery)
are implemented and tested — see `docs/CHANGELOG.md` for details and
known gaps. No real `ANTHROPIC_API_KEY` or live SMTP server has been
exercised yet (tests, CLI smoke tests, and the dashboard have all been
run against a fake AI client / fake SMTP connection / seeded fixture
data). Remaining: alerts, Ask MediaPulse (RAG), client portal polish,
Docker, scheduling (M5).

`mediapulse_platform.html` at the repo root is the original static design
reference for the frontend (landing page + app-shell mockup) — it predates
and is not served by the real `frontend/` React app.

## Layout

```
backend/
  mediapulse/
    config.py        # all env-driven settings; nothing else reads os.environ
    db.py             # SQLAlchemy engine/session
    models/           # Tenant, User, Topic, Source, Article, StoryCluster,
                       # Classification, Brief — all tenant-scoped
    cli.py            # `mediapulse ...` entrypoint (Typer)
    ingestion/
      dates.py          # masthead date recovery (weekday checksum)
      dedupe.py          # cross-outlet story clustering
      base.py            # shared IngestResult, content-hash, source health
      rss.py             # RSS/web monitoring worker
      pressreader.py     # PressReader connector interface (needs a real client)
      pdf.py             # layout-aware print PDF segmentation
      manual.py          # manual PDF/link upload path
      filters.py         # shared non-editorial (advert/notice) detection
    ai/
      client.py           # shared Anthropic SDK adapter (text + vision)
      json_utils.py        # markdown-fence stripping for model JSON output
      pricing.py            # per-model $/Mtok cost estimation
      vision_segment.py     # Claude-vision fallback for unresolved PDF pages
      schemas.py             # strict Pydantic schema for classification output
      prompts.py              # tenant-aware classification prompt builder
      classify.py              # classify_article/classify_pending (M2)
      brief_synthesis.py        # AI prose for the Daily Brief (M4)
    briefs/
      aggregate.py       # pillar/SOV/sentiment-shift/watchlist math (no AI)
      render.py           # Jinja2 -> email-safe HTML, WeasyPrint -> PDF
      generate.py          # aggregate -> synthesize -> render -> upsert Brief
    notify/
      email.py           # stdlib SMTP delivery (HTML + PDF attachment)
    scripts/
      import_legacy.py # legacy SQLite -> new schema, with date repair
      seed_demo_data.py # demo/dev fixture data (no API key needed)
    api/
      main.py            # FastAPI app, CORS, router registration
      deps.py             # DB session, current-user, tenant-scoping, RBAC
      routers/            # auth, articles, analytics, briefs, health
    schemas/            # Pydantic response models (API boundary validation)
  migrations/          # Alembic
  tests/
    fixtures/
      build_sample_pdfs.py  # generates synthetic Daily News / Gazette PDFs
    api/                # FastAPI TestClient tests
frontend/
  src/
    lib/                # api client, auth context, types, chart color rules
    components/         # Layout, StatTile, sentiment/threat badges
    pages/               # Login, Overview, StoryFeed, StoryDetail,
                         # ShareOfVoice, Briefs, Admin
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

## Running the full stack locally

```bash
# backend
cd backend && source .venv/bin/activate
export MEDIAPULSE_DATABASE_URL="sqlite:///./dev.db"
export MEDIAPULSE_SECRET_KEY="$(openssl rand -hex 32)"
alembic upgrade head
python -m mediapulse.cli seed-demo-tenant
python -m mediapulse.cli seed-demo-data --tenant orange-bw   # no API key needed
uvicorn mediapulse.api.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev   # proxies /api/* to localhost:8000, see vite.config.ts
```

`seed-demo-data` prints three demo logins (admin/analyst/client_viewer,
password `demo-password-123`) for the dashboard at http://localhost:5173.

## Generating a Daily Brief

Requires a real `ANTHROPIC_API_KEY` (the synthesis step calls the model
configured as `MEDIAPULSE_SYNTHESIS_MODEL`):

```bash
python -m mediapulse.cli brief --tenant orange-bw --date today --type daily
# add --send-to client@orange.bw to also email it (requires SMTP config in .env)
```

Writes the PDF to `MEDIAPULSE_BRIEF_STORAGE_DIR` (default `./brief_output`)
and upserts a `Brief` archive row — rerunning the same tenant/type/period
updates it in place. `--type` is `daily`/`weekly`/`monthly`.

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
