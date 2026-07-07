import json
import sqlite3
from pathlib import Path

from mediapulse.models import Article, ArticleStatus
from mediapulse.scripts.import_legacy import run_legacy_import

LEGACY_SCHEMA = """
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    topic_label TEXT,
    publication TEXT,
    url TEXT,
    title TEXT,
    published_at TEXT,
    fetched_at TEXT,
    content_hash TEXT,
    raw_text TEXT,
    status TEXT,
    classification TEXT,
    classified_at TEXT
);
"""


def _make_legacy_db(path: Path, rows: list[tuple]) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute(LEGACY_SCHEMA)
    conn.executemany(
        "INSERT INTO articles (topic_label, publication, url, title, published_at, "
        "fetched_at, content_hash, raw_text, status, classification, classified_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def test_legacy_import_repairs_garbage_print_date(tmp_path, session, tenant):
    db_path = tmp_path / "mediapulse.db"
    _make_legacy_db(
        db_path,
        [
            (
                "Orange Botswana (brand watch)",
                "Daily News",
                None,
                "Media Raises Freedom Concerns",
                "1780-46-43",  # legacy garbage date (defect #2)
                "2026-06-11 08:00:00",
                "hash-print-1",
                "Wednesday June 10, 2026 | No. 83\nMedia Raises Freedom Concerns\nBody text here that is long enough to count as real editorial content.",
                "classified",
                '{"model": "claude-sonnet-4-20250514"}',  # dead legacy classification, must be discarded
                "2026-06-11 09:00:00",
            ),
        ],
    )

    report = run_legacy_import(session=session, tenant=tenant, legacy_db_path=db_path)

    assert report.legacy_rows_read == 1
    assert report.imported == 1
    assert report.dates_repaired == 1

    article = session.query(Article).filter_by(tenant_id=tenant.id).one()
    assert article.published_at.isoformat().startswith("2026-06-10")
    assert article.published_at_confidence == "high"
    # legacy classification must never be trusted — always re-queued
    assert article.status == ArticleStatus.new


def test_legacy_import_flags_ocr_fragment_as_needs_review(tmp_path, session, tenant):
    db_path = tmp_path / "mediapulse.db"
    _make_legacy_db(
        db_path,
        [
            (
                "Orange Botswana (brand watch)",
                "Botswana Gazette",
                None,
                "ORANGE",  # masthead fragment mis-parsed as a headline
                "2026-05-06 08:00:00",
                "2026-05-06 08:00:00",
                "hash-fragment-1",
                "ORANGE",  # <60 chars, defect #3
                "classified",
                None,
                None,
            ),
        ],
    )

    report = run_legacy_import(session=session, tenant=tenant, legacy_db_path=db_path)

    assert report.flagged_needs_review == 1
    article = session.query(Article).filter_by(tenant_id=tenant.id).one()
    assert article.status == ArticleStatus.needs_review


def test_legacy_import_rejects_legal_notice(tmp_path, session, tenant):
    db_path = tmp_path / "mediapulse.db"
    _make_legacy_db(
        db_path,
        [
            (
                "Botswana business & fintech",
                "Botswana Gazette",
                None,
                "Legal Notice: Invitation to Tender",
                "2026-05-06 08:00:00",
                "2026-05-06 08:00:00",
                "hash-notice-1",
                "Invitation to Tender for the supply of office furniture to BOCRA regional offices, closing date 30 June 2026.",
                "classified",
                None,
                None,
            ),
        ],
    )

    report = run_legacy_import(session=session, tenant=tenant, legacy_db_path=db_path)

    assert report.rejected_as_non_editorial == 1
    article = session.query(Article).filter_by(tenant_id=tenant.id).one()
    assert article.status == ArticleStatus.rejected
    assert article.is_advert is True


def test_legacy_import_is_idempotent_on_rerun(tmp_path, session, tenant):
    db_path = tmp_path / "mediapulse.db"
    _make_legacy_db(
        db_path,
        [
            (
                "Orange Botswana (brand watch)",
                "Mmegi Online",
                "https://example.bw/story-1",
                "Orange Botswana expands network coverage",
                "2026-06-01 10:00:00",
                "2026-06-01 10:05:00",
                "hash-web-1",
                "Full web article body long enough to be real editorial content here.",
                "classified",
                None,
                None,
            ),
        ],
    )

    first = run_legacy_import(session=session, tenant=tenant, legacy_db_path=db_path)
    session.flush()
    second = run_legacy_import(session=session, tenant=tenant, legacy_db_path=db_path)

    assert first.imported == 1
    assert second.imported == 0
    assert second.skipped_duplicates == 1
    assert session.query(Article).filter_by(tenant_id=tenant.id).count() == 1


def test_legacy_import_report_written_to_disk(tmp_path, session, tenant):
    db_path = tmp_path / "mediapulse.db"
    _make_legacy_db(db_path, [])
    report = run_legacy_import(session=session, tenant=tenant, legacy_db_path=db_path)

    report_path = tmp_path / "report.json"
    report.write(report_path)
    payload = json.loads(report_path.read_text())
    assert payload["legacy_rows_read"] == 0
