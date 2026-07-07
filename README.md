# MediaPulse BW

AI-powered media intelligence platform for the PR/communications industry in
Botswana (DS Communications). Multi-tenant: the flagship tenant is Orange
Botswana, but any client (banks, mining, government, telcos) gets its own
watchlist, competitors, and topics.

See the delivery plan and full product brief in the original kickoff prompt;
this repo tracks it milestone by milestone in `docs/CHANGELOG.md`.

## Status

**M0 (scaffold), M1 (ingestion), M2 (AI enrichment), and M3 (API +
dashboard) are done.** RSS/PressReader ingestion, a layout-aware print PDF
pipeline, tenant-aware AI classification, a FastAPI backend, and a React
dashboard are implemented, tested, and verified end-to-end in a real
browser (login, story feed, story detail, share of voice, admin source
health) — see `docs/CHANGELOG.md` for details and known gaps. No real
`ANTHROPIC_API_KEY` has been exercised against the live API yet (tests,
CLI smoke tests, and the dashboard have all been run against a fake
client / seeded fixture data). Daily Brief generation (M4) is not built
yet — the archive UI/API are ready for it.

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
