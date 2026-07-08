"""AI enrichment: classification, per-brand sentiment, entities, summary,
and threat tagging for one article — plus the batch runner behind
`mediapulse classify`.

Same retry discipline as the vision fallback: a response that fails JSON
parsing or schema validation is retried up to `ai_max_retries` times
(config-driven) rather than trusted, and if every attempt fails the
article is marked `ArticleStatus.error` / `Classification.status=failed`
with the actual error recorded — that's the reprocessing queue defect #1
asked for. Nothing here reads a model name directly; it all comes from
`config.get_settings()`.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from dataclasses import dataclass, field

from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..alerts.rules import evaluate_article_alerts
from ..config import get_settings
from ..models import (
    Article,
    ArticleStatus,
    Classification,
    ClassificationStatus,
    Tenant,
    Topic,
)
from .client import AnthropicClient, AnthropicClientAdapter, text_block
from .json_utils import extract_json_object
from .pricing import estimate_cost_usd
from .prompts import build_classification_prompt
from .schemas import ClassificationResult


def _get_or_create_classification(session: Session, article: Article) -> Classification:
    existing = (
        session.query(Classification).filter_by(article_id=article.id).one_or_none()
    )
    if existing is not None:
        return existing
    classification = Classification(article_id=article.id, tenant_id=article.tenant_id)
    session.add(classification)
    session.flush()
    return classification


def classify_article(
    session: Session,
    article: Article,
    *,
    tenant: Tenant,
    topics: list[Topic],
    client: AnthropicClient | None = None,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
    now: dt.datetime | None = None,
) -> Classification:
    settings = get_settings()
    client = client or AnthropicClientAdapter()
    max_retries = max_retries if max_retries is not None else settings.ai_max_retries
    backoff_seconds = (
        backoff_seconds if backoff_seconds is not None else settings.ai_retry_backoff_seconds
    )
    now = now or dt.datetime.now(dt.timezone.utc)

    classification = _get_or_create_classification(session, article)
    article.status = ArticleStatus.processing
    session.flush()

    prompt = build_classification_prompt(tenant=tenant, topics=topics, article=article)
    content = [text_block(prompt)]

    total_input_tokens = 0
    total_output_tokens = 0
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        classification.attempt_count += 1
        try:
            result = client.create_message(model=settings.classify_model, content=content)
            total_input_tokens += result.input_tokens
            total_output_tokens += result.output_tokens

            payload = json.loads(extract_json_object(result.text))
            parsed = ClassificationResult.model_validate(payload)

            classification.status = ClassificationStatus.success
            classification.model_used = settings.classify_model
            classification.relevance_score = parsed.relevance_score
            classification.category = parsed.category
            classification.sentiment_overall = parsed.sentiment_overall
            classification.sentiment_by_brand = {
                brand: sentiment.value for brand, sentiment in parsed.sentiment_by_brand.items()
            }
            classification.entities = parsed.entities.model_dump()
            classification.summary_exec = parsed.summary_exec
            classification.key_quotes = parsed.key_quotes
            classification.why_it_matters = parsed.why_it_matters
            classification.threat_tag = parsed.threat_tag
            classification.threat_rationale = parsed.threat_rationale
            classification.tokens_in = total_input_tokens
            classification.tokens_out = total_output_tokens
            classification.cost_usd = estimate_cost_usd(
                settings.classify_model, total_input_tokens, total_output_tokens
            )
            classification.raw_response = payload
            classification.classified_at = now
            classification.error_message = None

            article.status = ArticleStatus.classified
            session.flush()
            evaluate_article_alerts(session, tenant, article)
            return classification
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
        except Exception as exc:  # noqa: BLE001 — API/network errors are also retryable
            last_error = exc

        if attempt < max_retries:
            time.sleep(backoff_seconds * attempt)

    classification.status = ClassificationStatus.failed
    classification.model_used = settings.classify_model
    classification.error_message = str(last_error)[:2000]
    classification.tokens_in = total_input_tokens
    classification.tokens_out = total_output_tokens
    classification.cost_usd = estimate_cost_usd(
        settings.classify_model, total_input_tokens, total_output_tokens
    )
    article.status = ArticleStatus.error
    session.flush()
    return classification


@dataclass
class ClassifyBatchResult:
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    total_cost_usd: float = 0.0
    failures: list[str] = field(default_factory=list)


def classify_pending(
    session: Session,
    *,
    tenant: Tenant,
    reprocess_errors: bool = False,
    client: AnthropicClient | None = None,
    limit: int | None = None,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
) -> ClassifyBatchResult:
    statuses = [ArticleStatus.new]
    if reprocess_errors:
        statuses.append(ArticleStatus.error)

    query = session.query(Article).filter(
        Article.tenant_id == tenant.id, Article.status.in_(statuses)
    )
    if limit is not None:
        query = query.limit(limit)
    articles = query.all()

    topics = session.query(Topic).filter_by(tenant_id=tenant.id).all()

    result = ClassifyBatchResult()
    for article in articles:
        classification = classify_article(
            session, article, tenant=tenant, topics=topics, client=client,
            max_retries=max_retries, backoff_seconds=backoff_seconds,
        )
        result.processed += 1
        result.total_cost_usd += classification.cost_usd or 0.0
        if classification.status == ClassificationStatus.success:
            result.succeeded += 1
        else:
            result.failed += 1
            result.failures.append(f"{article.title}: {classification.error_message}")

    return result
