"""AI-written prose for the Daily Brief: an executive summary, one short
commentary paragraph per pillar, a sentiment-shift narrative, and a
recommended action per watch-list item — all the numbers/rankings
themselves come from `briefs.aggregate.build_brief_data` (pure Python,
already tested); this module only asks the model to narrate what's
already been computed, in the house agency register.

Same retry discipline as classification and vision segmentation: bad JSON
is retried up to `ai_max_retries` times and a final failure raises clearly
rather than shipping a broken brief.
"""
from __future__ import annotations

import json
import time

from pydantic import BaseModel, Field, ValidationError

from ..briefs.aggregate import BriefData
from ..config import get_settings
from .client import AnthropicClient, AnthropicClientAdapter, text_block
from .json_utils import extract_json_object

_HOUSE_STYLE_RULES = """House style rules — follow exactly:
- Always write "Orange Digital Center" (US spelling "Center"), never "Centre".
- Professional agency register: concise, evidence-based, no hype.
- Do not invent facts not present in the story list below.
"""


class BriefSynthesisError(RuntimeError):
    pass


class BriefSynthesisResult(BaseModel):
    exec_summary: str
    pillar_commentary: dict[str, str] = Field(default_factory=dict)
    sentiment_commentary: str
    # article id -> one-line recommended action for that watch-list item
    watchlist_actions: dict[str, str] = Field(default_factory=dict)


def _format_pillar(pillar) -> str:
    lines = [f"{pillar.name} ({pillar.total_count} stories this period):"]
    for story in pillar.top_stories:
        c = story.classification
        lines.append(
            f"  - [{story.id}] \"{story.title}\" ({story.publication}, "
            f"sentiment={c.sentiment_overall.value if c.sentiment_overall else 'n/a'}, "
            f"threat={c.threat_tag.value if c.threat_tag else 'n/a'})"
        )
    return "\n".join(lines)


def _format_watchlist(data: BriefData) -> str:
    if not data.watchlist:
        return "(none)"
    lines = []
    for item in data.watchlist:
        lines.append(
            f"  - [{item.article.id}] \"{item.article.title}\" — {item.threat_tag.value}: {item.rationale}"
        )
    return "\n".join(lines)


def _format_sentiment_shifts(data: BriefData) -> str:
    if not data.sentiment_shifts:
        return "(no per-brand sentiment data this period)"
    lines = []
    for shift in data.sentiment_shifts:
        lines.append(f"  - {shift.brand}: previous={shift.previous or {}} -> current={shift.current or {}}")
    return "\n".join(lines)


def build_brief_prompt(data: BriefData) -> str:
    pillars_text = "\n".join(_format_pillar(p) for p in data.pillars) or "(no classified coverage this period)"
    sov_text = ", ".join(f"{brand}: {count}" for brand, count in sorted(
        data.share_of_voice.items(), key=lambda kv: -kv[1]
    )) or "(no brand mentions this period)"

    return f"""You are writing the Daily Brief for {data.tenant.name}, covering \
{data.period_start.isoformat()} to {data.period_end.isoformat()}. This is a professional \
PR/communications agency deliverable — concise exec summary first, evidence after.

{_HOUSE_STYLE_RULES}

Coverage by pillar (article ids in brackets):
{pillars_text}

Share of voice (mention counts, directional): {sov_text}

Sentiment shift vs. the preceding period of equal length:
{_format_sentiment_shifts(data)}

Watch-list items (Risk/Opportunity flagged stories):
{_format_watchlist(data)}

Return ONLY a JSON object of this exact shape:
{{
  "exec_summary": "2-4 sentence executive summary of the period as a whole",
  "pillar_commentary": {{"<pillar name>": "one short paragraph on that pillar", "...": "..."}},
  "sentiment_commentary": "one short paragraph narrating the sentiment shift data above",
  "watchlist_actions": {{"<article id>": "one-line recommended action for that item", "...": "..."}}
}}
Include a "pillar_commentary" entry for every pillar listed above, and a "watchlist_actions" \
entry for every watch-list item id listed above.
"""


def generate_brief_synthesis(
    data: BriefData,
    *,
    client: AnthropicClient | None = None,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
) -> BriefSynthesisResult:
    settings = get_settings()
    client = client or AnthropicClientAdapter()
    max_retries = max_retries if max_retries is not None else settings.ai_max_retries
    backoff_seconds = (
        backoff_seconds if backoff_seconds is not None else settings.ai_retry_backoff_seconds
    )

    prompt = build_brief_prompt(data)
    content = [text_block(prompt)]

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            result = client.create_message(model=settings.synthesis_model, content=content, max_tokens=4096)
            payload = json.loads(extract_json_object(result.text))
            return BriefSynthesisResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
        except Exception as exc:  # noqa: BLE001 — API/network errors are also retryable
            last_error = exc

        if attempt < max_retries:
            time.sleep(backoff_seconds * attempt)

    raise BriefSynthesisError(f"Brief synthesis failed after {max_retries} attempts: {last_error}")
