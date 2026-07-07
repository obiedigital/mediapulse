"""RSS/web monitoring worker.

Fetches raw feed bytes over HTTP separately from parsing (rather than
handing feedparser a URL directly) so the network call is a single
injectable seam — tests feed in canned XML without touching the network,
and production can add retry/timeout/proxy behaviour in one place.
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Callable

import feedparser
import httpx
from sqlalchemy.orm import Session

from ..models import Article, ArticleStatus, Source
from .base import IngestResult, compute_content_hash, record_source_error, record_source_success
from .dedupe import assign_story_cluster

Fetcher = Callable[[str], bytes]


def default_fetcher(url: str, *, timeout: float = 15.0) -> bytes:
    response = httpx.get(url, timeout=timeout, follow_redirects=True, headers={
        "User-Agent": "MediaPulseBW/0.1 (+https://mediapulse.bw)",
    })
    response.raise_for_status()
    return response.content


def _entry_published_at(entry) -> dt.datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        struct = entry.get(key)
        if struct:
            return dt.datetime.fromtimestamp(time.mktime(struct), tz=dt.timezone.utc)
    return None


def _entry_body(entry) -> str:
    if entry.get("content"):
        return entry["content"][0].get("value", "")
    return entry.get("summary", "") or entry.get("description", "")


def run(
    session: Session,
    source: Source,
    *,
    fetcher: Fetcher = default_fetcher,
    now: dt.datetime | None = None,
) -> IngestResult:
    result = IngestResult()
    now = now or dt.datetime.now(dt.timezone.utc)

    if not source.url:
        record_source_error(source, "RSS source has no url configured", now=now)
        result.errors.append("missing url")
        return result

    try:
        raw = fetcher(source.url)
        parsed = feedparser.parse(raw)
    except Exception as exc:  # noqa: BLE001 — network/parse failure is source-level
        record_source_error(source, str(exc), now=now)
        result.errors.append(str(exc))
        return result

    if parsed.bozo and not parsed.entries:
        message = str(parsed.get("bozo_exception", "unparseable feed"))
        record_source_error(source, message, now=now)
        result.errors.append(message)
        return result

    tenant_id = source.topic.tenant_id
    existing_hashes = {
        h for (h,) in session.query(Article.content_hash).filter_by(tenant_id=tenant_id)
    }
    feed_publication = getattr(parsed.feed, "title", None) or source.name

    for entry in parsed.entries:
        result.fetched += 1
        try:
            title = entry.get("title") or "(untitled)"
            url = entry.get("link")
            body = _entry_body(entry)
            content_hash = compute_content_hash(url=url, title=title, body=body)

            if content_hash in existing_hashes:
                result.skipped_duplicates += 1
                continue

            published_at = _entry_published_at(entry) or now

            article = Article(
                tenant_id=tenant_id,
                topic_id=source.topic_id,
                source_id=source.id,
                publication=feed_publication,
                title=title,
                url=url,
                published_at=published_at,
                published_at_confidence="high" if _entry_published_at(entry) else "low",
                fetched_at=now,
                content_hash=content_hash,
                raw_text=body,
                status=ArticleStatus.new,
            )
            session.add(article)
            session.flush()
            assign_story_cluster(session, article)

            existing_hashes.add(content_hash)
            result.inserted += 1
        except Exception as exc:  # noqa: BLE001 — one bad entry must not abort the feed
            result.errors.append(f"{entry.get('title', '?')!r}: {exc}")

    record_source_success(source, now=now)
    return result
