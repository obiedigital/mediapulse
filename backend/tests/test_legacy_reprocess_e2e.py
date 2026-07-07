"""End-to-end proof that defect #1 (classification pipeline dead on a
404ing model string) is actually fixed, not just individually unit-tested:
import the legacy corpus (which re-queues every row rather than trusting
the legacy classification columns) and then run it through the new
classification pipeline exactly as `mediapulse classify` would.
"""
import json
import sqlite3
from pathlib import Path

from mediapulse.ai.classify import classify_pending
from mediapulse.ai.client import MessageResult
from mediapulse.models import Article, ArticleStatus, ClassificationStatus
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

VALID_RESPONSE = json.dumps({
    "relevance_score": 0.8,
    "category": "government",
    "sentiment_overall": "neutral",
    "sentiment_by_brand": {},
    "entities": {"brands": [], "people": [], "organisations": ["Botswana Editors Forum"],
                 "products": [], "events": [], "locations": []},
    "summary_exec": "Media practitioners raised concerns over proposed access-to-information changes.",
    "key_quotes": [],
    "why_it_matters": "Regulatory changes to press freedom are directly relevant to the sector watchlist.",
    "threat_tag": "monitor",
    "threat_rationale": "Ongoing policy discussion, not yet a concrete threat.",
})


class FakeClient:
    def create_message(self, *, model, content, max_tokens=4096):
        return MessageResult(text=VALID_RESPONSE, input_tokens=300, output_tokens=150)


def _make_legacy_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute(LEGACY_SCHEMA)
    conn.execute(
        "INSERT INTO articles (topic_label, publication, url, title, published_at, "
        "fetched_at, content_hash, raw_text, status, classification, classified_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "Orange Botswana (brand watch)",
            "Daily News",
            None,
            "Media Raises Freedom Concerns",
            "1780-46-43",  # garbage legacy date, defect #2
            "2026-06-11 08:00:00",
            "hash-print-1",
            "Wednesday June 10, 2026 | No. 83\nMedia Raises Freedom Concerns\nMedia practitioners "
            "in Botswana have raised concerns over proposed amendments to access-to-information law.",
            "classified",
            # Legacy "classification" produced by a call to a 404ing model string —
            # must never be trusted or ported forward.
            '{"model": "claude-sonnet-4-20250514", "error": "404 model not found"}',
            "2026-06-11 09:00:00",
        ),
    )
    conn.commit()
    conn.close()


def test_legacy_import_then_classify_produces_real_intelligence(tmp_path, session, tenant):
    legacy_db_path = tmp_path / "mediapulse.db"
    _make_legacy_db(legacy_db_path)

    import_report = run_legacy_import(session=session, tenant=tenant, legacy_db_path=legacy_db_path)
    assert import_report.imported == 1
    assert import_report.dates_repaired == 1

    article = session.query(Article).filter_by(tenant_id=tenant.id).one()
    assert article.status == ArticleStatus.new  # re-queued, not carrying dead legacy output
    assert article.published_at.date().isoformat() == "2026-06-10"  # date bug fixed

    classify_result = classify_pending(
        session, tenant=tenant, client=FakeClient(), backoff_seconds=0
    )

    assert classify_result.processed == 1
    assert classify_result.succeeded == 1
    session.refresh(article)
    assert article.status == ArticleStatus.classified
    assert article.classification.status == ClassificationStatus.success
    assert article.classification.model_used != "claude-sonnet-4-20250514"
    assert "Botswana Editors Forum" in article.classification.entities["organisations"]
