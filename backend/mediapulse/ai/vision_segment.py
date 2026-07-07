"""Vision fallback for print pages the heuristic segmenter can't resolve.

`ingestion.pdf.segment_pdf` flags a page in `pages_needing_vision_fallback`
when it finds no headline-sized text and no real body content — usually a
heavily degraded scan. Rather than guess, this module sends that page's
rendered image to a vision-capable Claude model and asks for the same
structured shape (`headline`/`byline`/`body`/`page`/`section`) the
heuristic path produces, so callers can merge the two without caring which
one ran.

The model client is injected (`AnthropicMessagesClient` protocol) so this
is testable without a network call or an API key — `AnthropicClientAdapter`
is the real implementation, constructed lazily so importing this module
never requires the `anthropic` package to be configured.

Bad/unparseable model output is retried up to `ai_max_retries` times
(config-driven, not hardcoded) rather than trusted or silently discarded —
this is the same lesson as defect #1: a model call that returns garbage
must be visible, not swallowed.
"""
from __future__ import annotations

import base64
import json
import re
import time
from typing import Protocol

import fitz
from pydantic import BaseModel, ValidationError

from ..config import get_settings

SEGMENTATION_PROMPT = """You are segmenting one page of a Botswana print newspaper into articles.

Return ONLY a JSON object of the form:
{{"articles": [{{"headline": "...", "byline": "..." or null, "body": "...", "section": "..." or null, "is_advert": false}}]}}

Rules:
- One entry per distinct article. Merge wrapped/multi-column body text for the same article into one "body" string.
- Set "is_advert": true for adverts, legal notices, tenders, classifieds, or rate/exchange tables — still include them, don't drop them, just flag them.
- Do not include the masthead, running headers, or page numbers as articles.
- "byline" is the reporter credit line (e.g. "By Staff Reporter") if present, else null.
- This is page {page} of the document.
"""


class VisionSegmentedArticle(BaseModel):
    headline: str
    byline: str | None = None
    body: str
    # Not part of the model's JSON schema — the caller already knows which
    # page it sent, so `segment_page_with_vision` stamps this after parsing.
    page: int = 0
    section: str | None = None
    is_advert: bool = False


class VisionSegmentationResponse(BaseModel):
    articles: list[VisionSegmentedArticle]


class VisionSegmentationError(RuntimeError):
    pass


class AnthropicMessagesClient(Protocol):
    def create_message(self, *, model: str, image_b64: str, prompt: str) -> str: ...


class AnthropicClientAdapter:
    """Thin wrapper around the real Anthropic SDK, constructed lazily so
    this module imports cleanly with no API key configured."""

    def __init__(self, api_key: str | None = None):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key or get_settings().anthropic_api_key)

    def create_message(self, *, model: str, image_b64: str, prompt: str) -> str:
        response = self._client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": image_b64},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return "".join(block.text for block in response.content if block.type == "text")


def render_page_png(pdf_path: str, page_number: int, *, dpi: int = 200) -> bytes:
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_number - 1]
        return page.get_pixmap(dpi=dpi).tobytes("png")
    finally:
        doc.close()


def _extract_json(text: str) -> str:
    """Strip a ```json ... ``` fence if the model wrapped its output in one."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    return text


def segment_page_with_vision(
    pdf_path: str,
    page_number: int,
    *,
    client: AnthropicMessagesClient | None = None,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
) -> list[VisionSegmentedArticle]:
    settings = get_settings()
    client = client or AnthropicClientAdapter()
    max_retries = max_retries if max_retries is not None else settings.ai_max_retries
    backoff_seconds = (
        backoff_seconds if backoff_seconds is not None else settings.ai_retry_backoff_seconds
    )

    image_b64 = base64.b64encode(render_page_png(pdf_path, page_number)).decode()
    prompt = SEGMENTATION_PROMPT.format(page=page_number)

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            raw = client.create_message(model=settings.vision_model, image_b64=image_b64, prompt=prompt)
            payload = json.loads(_extract_json(raw))
            parsed = VisionSegmentationResponse.model_validate(payload)
            for article in parsed.articles:
                article.page = page_number
            return parsed.articles
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
        except Exception as exc:  # noqa: BLE001 — API/network errors are also retryable
            last_error = exc

        if attempt < max_retries:
            time.sleep(backoff_seconds * attempt)

    raise VisionSegmentationError(
        f"Vision segmentation failed after {max_retries} attempts for page {page_number}: {last_error}"
    )
