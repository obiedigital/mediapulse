"""PressReader connector.

PressReader has no public article-content API — the legacy Colab prototype
scraped an authenticated reader session, and that scraping code isn't part
of this repo. Rather than guess at scraping logic that could break silently
or violate PressReader's terms, this module defines the seam a real
implementation plugs into (`PressReaderClient`) and wires the same
insert/dedupe/health-tracking path the RSS worker uses, so swapping in a
working scraper later is a one-file change with no orchestration risk.

Until then, `run()` with no client configured fails loudly and specifically
("PressReader client not configured") via the normal source-health error
path, instead of crashing or silently no-op'ing.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from ..models import Article, ArticleStatus, Source
from .base import IngestResult, compute_content_hash, record_source_error, record_source_success
from .dedupe import assign_story_cluster


@dataclass
class PressReaderArticle:
    title: str
    body: str
    publication: str
    published_at: dt.datetime
    url: str | None = None
    byline: str | None = None
    page_number: int | None = None


class PressReaderClient(Protocol):
    """Implement this against a real authenticated PressReader session."""

    def fetch_recent_articles(
        self, *, publication_id: str, since: dt.datetime
    ) -> list[PressReaderArticle]: ...


class PressReaderNotConfigured(RuntimeError):
    pass


def run(
    session: Session,
    source: Source,
    *,
    client: PressReaderClient | None = None,
    now: dt.datetime | None = None,
) -> IngestResult:
    result = IngestResult()
    now = now or dt.datetime.now(dt.timezone.utc)

    publication_id = (source.config or {}).get("publication_id")
    if not publication_id:
        record_source_error(source, "PressReader source has no publication_id configured", now=now)
        result.errors.append("missing publication_id")
        return result

    if client is None:
        message = (
            "PressReader client not configured — set up credentials and pass a "
            "PressReaderClient implementation (see ingestion/pressreader.py)."
        )
        record_source_error(source, message, now=now)
        result.errors.append(message)
        return result

    since = source.last_success_at or (now - dt.timedelta(days=7))

    try:
        articles = client.fetch_recent_articles(publication_id=publication_id, since=since)
    except Exception as exc:  # noqa: BLE001 — connector-level failure
        record_source_error(source, str(exc), now=now)
        result.errors.append(str(exc))
        return result

    tenant_id = source.topic.tenant_id
    existing_hashes = {
        h for (h,) in session.query(Article.content_hash).filter_by(tenant_id=tenant_id)
    }

    for pr_article in articles:
        result.fetched += 1
        try:
            content_hash = compute_content_hash(
                url=pr_article.url, title=pr_article.title, body=pr_article.body
            )
            if content_hash in existing_hashes:
                result.skipped_duplicates += 1
                continue

            article = Article(
                tenant_id=tenant_id,
                topic_id=source.topic_id,
                source_id=source.id,
                publication=pr_article.publication,
                title=pr_article.title,
                byline=pr_article.byline,
                url=pr_article.url,
                page_number=pr_article.page_number,
                published_at=pr_article.published_at,
                published_at_confidence="high",
                fetched_at=now,
                content_hash=content_hash,
                raw_text=pr_article.body,
                status=ArticleStatus.new,
            )
            session.add(article)
            session.flush()
            assign_story_cluster(session, article)

            existing_hashes.add(content_hash)
            result.inserted += 1
        except Exception as exc:  # noqa: BLE001 — one bad article must not abort the batch
            result.errors.append(f"{pr_article.title!r}: {exc}")

    record_source_success(source, now=now)
    return result
