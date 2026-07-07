"""Manual upload path: a coordinator drops a PDF or pastes a link through
the UI (M3) — this module is the backend half of that, callable directly
from the CLI ahead of the UI existing.

`ingest_pdf` runs the full print pipeline (heuristic segmentation, optional
vision fallback for pages it couldn't resolve, masthead-date resolution)
and inserts one `Article` per segmented item, same as an automated PDF
source would. `ingest_link` is a thin single-URL fetch for "just add this
one story" — it does not attempt the RSS worker's feed-level batching.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from ..ai.vision_segment import VisionSegmentationError, segment_page_with_vision
from ..models import Article, ArticleStatus, Tenant, Topic
from .base import IngestResult, compute_content_hash
from .dedupe import assign_story_cluster
from .pdf import SegmentedArticle, segment_pdf
from .rss import Fetcher, default_fetcher


def ingest_pdf(
    session: Session,
    *,
    tenant: Tenant,
    topic: Topic,
    pdf_path: str | Path,
    publication: str,
    source_id: str | None = None,
    use_vision_fallback: bool = True,
    vision_client=None,
    now: dt.datetime | None = None,
) -> IngestResult:
    result = IngestResult()
    now = now or dt.datetime.now(dt.timezone.utc)

    seg = segment_pdf(pdf_path)
    articles_to_insert: list[SegmentedArticle] = list(seg.articles)

    if use_vision_fallback and seg.pages_needing_vision_fallback:
        fallback_pages = set(seg.pages_needing_vision_fallback)
        # Drop heuristic fragments that came *only* from a page we're about
        # to re-segment with vision, so we don't double-insert the same page.
        articles_to_insert = [
            a for a in articles_to_insert if not set(a.pages) <= fallback_pages
        ]
        for page_number in seg.pages_needing_vision_fallback:
            try:
                vision_articles = segment_page_with_vision(
                    str(pdf_path), page_number, client=vision_client
                )
                for va in vision_articles:
                    articles_to_insert.append(
                        SegmentedArticle(
                            headline=va.headline,
                            body=va.body,
                            byline=va.byline,
                            pages=[page_number],
                            is_advert=va.is_advert,
                        )
                    )
            except VisionSegmentationError as exc:
                result.errors.append(f"page {page_number}: {exc}")

    published_at = (
        dt.datetime.combine(seg.masthead_date, dt.time.min, tzinfo=dt.timezone.utc)
        if seg.masthead_date is not None
        else now
    )
    date_confidence = "high" if seg.masthead_date is not None else "low"

    tenant_id = tenant.id
    existing_hashes = {
        h for (h,) in session.query(Article.content_hash).filter_by(tenant_id=tenant_id)
    }

    for seg_article in articles_to_insert:
        result.fetched += 1
        try:
            content_hash = compute_content_hash(
                url=None, title=seg_article.headline, body=seg_article.body
            )
            if content_hash in existing_hashes:
                result.skipped_duplicates += 1
                continue

            if seg_article.is_advert:
                status = ArticleStatus.rejected
                result.rejected_non_editorial += 1
            elif date_confidence == "low":
                status = ArticleStatus.needs_review
            else:
                status = ArticleStatus.new

            article = Article(
                tenant_id=tenant_id,
                topic_id=topic.id,
                source_id=source_id,
                publication=publication,
                title=seg_article.headline,
                byline=seg_article.byline,
                page_number=seg_article.pages[0] if seg_article.pages else None,
                is_advert=seg_article.is_advert,
                published_at=published_at,
                published_at_raw=seg.masthead_date_raw,
                published_at_confidence=date_confidence,
                fetched_at=now,
                content_hash=content_hash,
                raw_text=seg_article.body,
                status=status,
            )
            session.add(article)
            session.flush()
            if not seg_article.is_advert:
                assign_story_cluster(session, article)

            existing_hashes.add(content_hash)
            result.inserted += 1
        except Exception as exc:  # noqa: BLE001 — one bad article must not abort the batch
            result.errors.append(f"{seg_article.headline!r}: {exc}")

    return result


def ingest_link(
    session: Session,
    *,
    tenant: Tenant,
    topic: Topic,
    url: str,
    source_id: str | None = None,
    fetcher: Fetcher = default_fetcher,
    now: dt.datetime | None = None,
) -> IngestResult:
    result = IngestResult()
    now = now or dt.datetime.now(dt.timezone.utc)

    try:
        raw = fetcher(url)
    except Exception as exc:  # noqa: BLE001
        result.errors.append(str(exc))
        return result

    result.fetched = 1
    soup = BeautifulSoup(raw, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    body = soup.get_text(separator=" ", strip=True)

    content_hash = compute_content_hash(url=url, title=title, body=body)
    if session.query(Article).filter_by(tenant_id=tenant.id, content_hash=content_hash).first():
        result.skipped_duplicates = 1
        return result

    article = Article(
        tenant_id=tenant.id,
        topic_id=topic.id,
        source_id=source_id,
        publication=httpx.URL(url).host or "Unknown",
        title=title,
        url=url,
        published_at=now,
        published_at_confidence="low",
        fetched_at=now,
        content_hash=content_hash,
        raw_text=body,
        status=ArticleStatus.new,
    )
    session.add(article)
    session.flush()
    assign_story_cluster(session, article)
    result.inserted = 1
    return result
