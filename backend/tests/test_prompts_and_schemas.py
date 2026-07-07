import datetime as dt

import pytest
from pydantic import ValidationError

from mediapulse.ai.prompts import build_classification_prompt
from mediapulse.ai.schemas import ClassificationResult
from mediapulse.models import Article, Topic, TopicKind


def test_classification_result_accepts_full_valid_payload():
    payload = {
        "relevance_score": 0.9,
        "category": "telco",
        "sentiment_overall": "neutral",
        "sentiment_by_brand": {"Orange Botswana": "neutral", "BTC": "negative"},
        "entities": {"brands": ["Orange Botswana", "BTC"], "people": ["Minister X"]},
        "summary_exec": "Two sentence summary.",
        "key_quotes": ["quote one"],
        "why_it_matters": "Because reasons.",
        "threat_tag": "monitor",
        "threat_rationale": "Routine competitor news.",
    }
    result = ClassificationResult.model_validate(payload)
    assert result.sentiment_by_brand["BTC"].value == "negative"
    assert result.entities.people == ["Minister X"]


def test_classification_result_rejects_relevance_out_of_range():
    payload = {
        "relevance_score": 1.5,
        "category": "telco",
        "sentiment_overall": "neutral",
        "summary_exec": "x",
        "why_it_matters": "x",
        "threat_tag": "monitor",
        "threat_rationale": "x",
    }
    with pytest.raises(ValidationError):
        ClassificationResult.model_validate(payload)


def test_classification_result_rejects_invalid_sentiment_enum():
    payload = {
        "relevance_score": 0.5,
        "category": "telco",
        "sentiment_overall": "furious",
        "summary_exec": "x",
        "why_it_matters": "x",
        "threat_tag": "monitor",
        "threat_rationale": "x",
    }
    with pytest.raises(ValidationError):
        ClassificationResult.model_validate(payload)


def test_classification_result_defaults_entities_and_quotes_to_empty():
    payload = {
        "relevance_score": 0.5,
        "category": "other",
        "sentiment_overall": "neutral",
        "summary_exec": "x",
        "why_it_matters": "x",
        "threat_tag": "monitor",
        "threat_rationale": "x",
    }
    result = ClassificationResult.model_validate(payload)
    assert result.entities.brands == []
    assert result.key_quotes == []
    assert result.sentiment_by_brand == {}


def test_prompt_injects_tenant_watchlist_and_article(tenant):
    topics = [
        Topic(tenant_id=tenant.id, label="Orange Botswana (brand watch)", kind=TopicKind.brand_watch,
              keywords=["Orange Botswana", "Orange Money"]),
        Topic(tenant_id=tenant.id, label="Mascom & BTC (competitors)", kind=TopicKind.competitor,
              keywords=["Mascom", "BTC"]),
    ]
    article = Article(
        tenant_id=tenant.id,
        topic_id="unused-in-prompt",
        publication="Mmegi Online",
        title="BTC cuts data prices",
        published_at=dt.datetime.now(dt.timezone.utc),
        fetched_at=dt.datetime.now(dt.timezone.utc),
        content_hash="x",
        raw_text="BTC announced a 20% cut in data bundle prices today.",
    )

    prompt = build_classification_prompt(tenant=tenant, topics=topics, article=article)

    assert tenant.name in prompt
    assert "Orange Botswana (brand watch)" in prompt
    assert "Mascom & BTC (competitors)" in prompt
    assert "BTC cuts data prices" in prompt
    assert "BTC announced a 20% cut" in prompt
    assert "sentiment_by_brand" in prompt


def test_prompt_truncates_very_long_body(tenant):
    article = Article(
        tenant_id=tenant.id,
        topic_id="unused-in-prompt",
        publication="Mmegi Online",
        title="Long article",
        published_at=dt.datetime.now(dt.timezone.utc),
        fetched_at=dt.datetime.now(dt.timezone.utc),
        content_hash="y",
        raw_text="word " * 5000,
    )

    prompt = build_classification_prompt(tenant=tenant, topics=[], article=article)

    assert "[...truncated...]" in prompt
    assert "(no watchlist configured)" in prompt
