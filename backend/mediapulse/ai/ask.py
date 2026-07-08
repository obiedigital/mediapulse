"""Ask MediaPulse: a strategist's question over the tenant's corpus,
answered with citations to stored articles.

Retrieval is plain lexical scoring (query-term overlap against title/body/
summary) rather than embeddings — this is the "Postgres full-text search
to start" phase the product brief calls for; swap in pgvector similarity
once corpus size actually warrants it, without touching
`ask_mediapulse`'s interface (retrieval is a single seam, `search_articles`).

Same retry discipline as classification/vision/brief synthesis: bad JSON
is retried, and a final failure raises `AskError` clearly.
"""
from __future__ import annotations

import json
import re
import time

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session, joinedload

from ..config import get_settings
from ..models import Article, ClassificationStatus, Tenant
from .client import AnthropicClient, AnthropicClientAdapter, text_block
from .json_utils import extract_json_object

_STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "for", "to", "and", "or", "with",
    "at", "by", "is", "are", "was", "were", "how", "what", "when", "did",
    "does", "compare", "compared", "vs", "versus", "this", "that", "it",
}

MAX_BODY_EXCERPT_CHARS = 600


class AskCitation(BaseModel):
    article_id: str
    title: str


class AskResult(BaseModel):
    answer: str
    citations: list[AskCitation] = Field(default_factory=list)


class AskError(RuntimeError):
    pass


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def search_articles(session: Session, tenant: Tenant, query: str, *, limit: int = 8) -> list[Article]:
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    candidates = (
        session.query(Article)
        .options(joinedload(Article.classification), joinedload(Article.topic))
        .filter(Article.tenant_id == tenant.id)
        .all()
    )

    scored: list[tuple[float, Article]] = []
    for article in candidates:
        c = article.classification
        title_terms = _tokenize(article.title)
        body_terms = _tokenize((article.raw_text or "")[:2000])
        summary_terms = _tokenize(c.summary_exec) if c and c.summary_exec else set()

        score = (
            3 * len(query_terms & title_terms)
            + 2 * len(query_terms & summary_terms)
            + len(query_terms & body_terms)
        )
        if c is not None and c.status == ClassificationStatus.success:
            score += 0.5  # slight preference for enriched articles, all else equal
        if score > 0:
            scored.append((score, article))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [article for _, article in scored[:limit]]


def _format_article(article: Article) -> str:
    c = article.classification
    excerpt = (article.raw_text or "")[:MAX_BODY_EXCERPT_CHARS]
    summary = f" Summary: {c.summary_exec}" if c and c.summary_exec else ""
    date = (article.published_at or article.fetched_at).date().isoformat()
    return (
        f'[{article.id}] "{article.title}" — {article.publication}, {date}.{summary}\n'
        f"Excerpt: {excerpt}"
    )


def build_ask_prompt(*, tenant: Tenant, question: str, articles: list[Article]) -> str:
    if not articles:
        context = "(no matching articles found in the corpus)"
    else:
        context = "\n\n".join(_format_article(a) for a in articles)

    return f"""You are answering a question for a media strategist at {tenant.name} using only the \
articles retrieved from their MediaPulse corpus below. Do not use outside knowledge. If the \
retrieved articles don't contain enough information to answer, say so plainly rather than guessing.

Retrieved articles (article ids in brackets):
{context}

Question: {question}

Return ONLY a JSON object of this exact shape:
{{"answer": "your answer, citing specifics from the articles above", "citations": [{{"article_id": "...", "title": "..."}}]}}
Only cite articles you actually used to answer. If you cannot answer from the articles provided, \
set "citations" to an empty list and say so in "answer".
"""


def ask_mediapulse(
    session: Session,
    tenant: Tenant,
    question: str,
    *,
    client: AnthropicClient | None = None,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
    limit: int = 8,
) -> AskResult:
    settings = get_settings()
    client = client or AnthropicClientAdapter()
    max_retries = max_retries if max_retries is not None else settings.ai_max_retries
    backoff_seconds = (
        backoff_seconds if backoff_seconds is not None else settings.ai_retry_backoff_seconds
    )

    articles = search_articles(session, tenant, question, limit=limit)
    prompt = build_ask_prompt(tenant=tenant, question=question, articles=articles)
    content = [text_block(prompt)]

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            result = client.create_message(model=settings.synthesis_model, content=content, max_tokens=2048)
            payload = json.loads(extract_json_object(result.text))
            return AskResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
        except Exception as exc:  # noqa: BLE001 — API/network errors are also retryable
            last_error = exc

        if attempt < max_retries:
            time.sleep(backoff_seconds * attempt)

    raise AskError(f"Ask MediaPulse failed after {max_retries} attempts: {last_error}")
