"""Shared plumbing for ingestion workers (RSS, PressReader, PDF, manual).

Every worker returns an `IngestResult` and updates the `Source` health
fields the same way, so the admin source-health page (last fetch, error
streak) is uniform regardless of connector type — this is also what lets
the M1 brief's "future connectors: social media, broadcast transcripts,
Google Alerts" slot in later without touching the orchestration layer.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass, field

from ..models import Source


@dataclass
class IngestResult:
    fetched: int = 0
    inserted: int = 0
    skipped_duplicates: int = 0
    rejected_non_editorial: int = 0
    errors: list[str] = field(default_factory=list)


def record_source_success(source: Source, *, now: dt.datetime | None = None) -> None:
    now = now or dt.datetime.now(dt.timezone.utc)
    source.last_fetched_at = now
    source.last_success_at = now
    source.consecutive_error_count = 0
    source.last_error = None


def record_source_error(source: Source, message: str, *, now: dt.datetime | None = None) -> None:
    now = now or dt.datetime.now(dt.timezone.utc)
    source.last_fetched_at = now
    source.consecutive_error_count += 1
    source.last_error = message[:2000]


def compute_content_hash(*, url: str | None, title: str, body: str = "") -> str:
    """Stable identity for an ingested item, independent of re-fetch timing.

    Prefers the canonical URL (present for web/RSS items); print items with
    no URL fall back to title+body so re-running the same PDF is idempotent.
    """
    basis = url if url else f"{title}|{body[:500]}"
    return hashlib.sha256(basis.encode("utf-8", errors="ignore")).hexdigest()
