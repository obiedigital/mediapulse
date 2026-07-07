"""Cross-outlet story clustering.

Two separate concerns, both called "dedup" loosely but distinct:

  * exact-duplicate guard — `content_hash` equality, checked by each
    ingestion worker before insert (same item re-fetched on a rerun).
  * story clustering — the *same real-world story* picked up by several
    outlets with different bylines/wording. That's what this module does:
    fuzzy-match a new article's title against recently-seen clusters for
    the tenant and either join an existing `StoryCluster` or start one.
    `pickup_count` on the resulting cluster is the reach signal used in
    SOV charts and the Daily Brief.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from ..models import Article, StoryCluster

_STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "for", "to", "and", "or", "with",
    "at", "by", "is", "as", "over", "after", "amid", "amid", "into",
}

DEFAULT_WINDOW_DAYS = 5
DEFAULT_SIMILARITY_THRESHOLD = 86


def normalize_title(title: str) -> str:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return " ".join(w for w in words if w not in _STOPWORDS)


def fingerprint(title: str) -> str:
    """Cheap key for indexed lookups; not itself the similarity check."""
    normalized = normalize_title(title)
    return hashlib.sha1(normalized.encode()).hexdigest()[:16]


def title_similarity(a: str, b: str) -> float:
    return fuzz.token_sort_ratio(normalize_title(a), normalize_title(b))


def assign_story_cluster(
    session: Session,
    article: Article,
    *,
    window_days: int = DEFAULT_WINDOW_DAYS,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> StoryCluster:
    """Attach `article` to an existing cluster if a similar-enough title was
    seen for this tenant within the recency window, else start a new one.

    Mutates and flushes `article` (sets `story_cluster_id`) and the chosen
    cluster (pickup_count, last_seen_at) but does not commit.
    """
    reference_time = article.published_at or article.fetched_at
    window_start = reference_time - dt.timedelta(days=window_days)

    candidates = (
        session.query(StoryCluster)
        .filter(
            StoryCluster.tenant_id == article.tenant_id,
            StoryCluster.last_seen_at >= window_start,
        )
        .all()
    )

    best_cluster: StoryCluster | None = None
    best_score = 0.0
    for cluster in candidates:
        if cluster.primary_article_id is None:
            continue
        primary = session.get(Article, cluster.primary_article_id)
        if primary is None or primary.id == article.id:
            continue
        score = title_similarity(article.title, primary.title)
        if score > best_score:
            best_score = score
            best_cluster = cluster

    if best_cluster is not None and best_score >= similarity_threshold:
        best_cluster.pickup_count += 1
        best_cluster.last_seen_at = max(best_cluster.last_seen_at, reference_time)
        article.story_cluster_id = best_cluster.id
        session.flush()
        return best_cluster

    cluster = StoryCluster(
        tenant_id=article.tenant_id,
        cluster_key=fingerprint(article.title),
        primary_article_id=article.id,
        pickup_count=1,
        first_seen_at=reference_time,
        last_seen_at=reference_time,
    )
    session.add(cluster)
    session.flush()
    article.story_cluster_id = cluster.id
    session.flush()
    return cluster
