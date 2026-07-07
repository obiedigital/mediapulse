"""One-shot importer for the legacy Colab-era SQLite corpus.

Ports the legacy `articles` table into the new multi-tenant schema, fixing
the two defects that made the legacy data unusable on read:

  * defect #1 (classification pipeline dead on a 404ing model string) —
    every imported row is re-queued (`ArticleStatus.new`) rather than
    trusting the legacy `classification`/`classified_at` columns, which
    were produced by calls that were silently failing.
  * defect #2 (print dates are the fetch date or garbage like
    "1780-46-43") — `mediapulse.ingestion.dates.resolve_published_at`
    re-derives the true date from the masthead text and records how
    confident it is.

It does *not* attempt full article re-segmentation (defect #3 — OCR
fragmentation) since that requires the rebuilt PDF pipeline (M1) working
from the original PDFs, which the legacy DB no longer has. It does apply a
cheap heuristic to flag/reject the worst fragments and non-editorial
content so they stop polluting coverage counts immediately.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from ..ingestion.dates import DateConfidence, resolve_published_at
from ..models import Article, ArticleStatus, Tenant, Topic, TopicKind

MIN_EDITORIAL_BODY_CHARS = 60

_NON_EDITORIAL_KEYWORDS = (
    "invitation to tender",
    "tender notice",
    "legal notice",
    "notice of intention",
    "public notice",
    "classifieds",
    "rate table",
    "advertisement feature",
)


@dataclass
class LegacyImportReport:
    legacy_rows_read: int = 0
    imported: int = 0
    skipped_duplicates: int = 0
    dates_repaired: int = 0
    rejected_as_non_editorial: int = 0
    flagged_needs_review: int = 0
    parse_errors: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def write(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.__dict__, indent=2, default=str))


def _parse_legacy_datetime(value: str | None) -> dt.datetime | None:
    """Parse a legacy timestamp column, returning None for anything that
    isn't a real calendar datetime (covers the "1780-46-43" class of bug)."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = dt.datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    try:
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except ValueError:
        return None


def _looks_non_editorial(title: str, raw_text: str) -> bool:
    haystack = f"{title}\n{raw_text[:500]}".lower()
    return any(keyword in haystack for keyword in _NON_EDITORIAL_KEYWORDS)


def _get_or_create_topic(session: Session, tenant: Tenant, topic_label: str | None) -> Topic:
    label = topic_label or "Uncategorised (legacy import)"
    topic = (
        session.query(Topic)
        .filter_by(tenant_id=tenant.id, label=label)
        .one_or_none()
    )
    if topic is None:
        topic = Topic(tenant_id=tenant.id, label=label, kind=TopicKind.custom, keywords=[])
        session.add(topic)
        session.flush()
    return topic


def run_legacy_import(
    *,
    session: Session,
    tenant: Tenant,
    legacy_db_path: Path,
    dashboard_json_path: Path | None = None,
) -> LegacyImportReport:
    report = LegacyImportReport()
    now = dt.datetime.now(dt.timezone.utc)

    conn = sqlite3.connect(str(legacy_db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM articles").fetchall()
    finally:
        conn.close()

    existing_hashes = {
        h for (h,) in session.query(Article.content_hash).filter_by(tenant_id=tenant.id)
    }

    for row in rows:
        report.legacy_rows_read += 1
        row_id = row["id"] if "id" in row.keys() else None
        try:
            raw_text = row["raw_text"] or ""
            title = row["title"] or "(untitled)"
            content_hash = row["content_hash"] or hashlib.sha256(raw_text.encode()).hexdigest()

            if content_hash in existing_hashes:
                report.skipped_duplicates += 1
                continue

            fetched_at = _parse_legacy_datetime(row["fetched_at"]) or now
            legacy_published_at = _parse_legacy_datetime(row["published_at"])

            published_at, raw_match, confidence = resolve_published_at(
                raw_text,
                fetched_at=fetched_at,
                existing_published_at=legacy_published_at,
            )
            date_was_repaired = (
                legacy_published_at is None
                or legacy_published_at.date() != published_at.date()
            )
            if date_was_repaired:
                report.dates_repaired += 1

            is_fragment = len(raw_text.strip()) < MIN_EDITORIAL_BODY_CHARS
            is_non_editorial = _looks_non_editorial(title, raw_text)

            if is_non_editorial:
                status = ArticleStatus.rejected
                report.rejected_as_non_editorial += 1
            elif is_fragment or confidence == DateConfidence.LOW:
                status = ArticleStatus.needs_review
                report.flagged_needs_review += 1
            else:
                status = ArticleStatus.new

            topic = _get_or_create_topic(session, tenant, row["topic_label"] if "topic_label" in row.keys() else None)

            article = Article(
                tenant_id=tenant.id,
                topic_id=topic.id,
                publication=row["publication"] or "Unknown",
                title=title,
                url=row["url"] if "url" in row.keys() else None,
                is_advert=is_non_editorial,
                published_at=published_at,
                published_at_raw=raw_match,
                published_at_confidence=confidence.value,
                fetched_at=fetched_at,
                content_hash=content_hash,
                raw_text=raw_text,
                status=status,
            )
            session.add(article)
            existing_hashes.add(content_hash)
            report.imported += 1
        except Exception as exc:  # noqa: BLE001 — one bad row must not abort the run
            report.parse_errors.append({"legacy_id": row_id, "error": str(exc)})

    if dashboard_json_path is not None and Path(dashboard_json_path).exists():
        try:
            payload = json.loads(Path(dashboard_json_path).read_text())
            story_count = len(payload.get("stories", [])) if isinstance(payload, dict) else None
            report.notes.append(
                f"dashboard_data.json contained {story_count} stories (not imported as "
                "source of truth — legacy classification output is discarded per defect #1)."
            )
        except (json.JSONDecodeError, OSError) as exc:
            report.notes.append(f"Could not read dashboard_data.json: {exc}")

    return report
