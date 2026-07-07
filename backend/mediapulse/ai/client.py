"""Single seam for every Anthropic API call in the codebase.

Both text classification (`ai/classify.py`) and vision-based PDF page
segmentation (`ai/vision_segment.py`) go through this one adapter, so
there is exactly one place that constructs the SDK client, reads the model
string, and records token usage — the M0 outage happened because the
model id was buried inline in a worker instead of centralized like this.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..config import get_settings


@dataclass
class MessageResult:
    text: str
    input_tokens: int
    output_tokens: int


class AnthropicClient(Protocol):
    def create_message(
        self, *, model: str, content: list[dict], max_tokens: int = 4096
    ) -> MessageResult: ...


class AnthropicClientAdapter:
    """Thin wrapper around the real Anthropic SDK, constructed lazily so
    importing callers never requires an API key to be configured."""

    def __init__(self, api_key: str | None = None):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key or get_settings().anthropic_api_key)

    def create_message(
        self, *, model: str, content: list[dict], max_tokens: int = 4096
    ) -> MessageResult:
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return MessageResult(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


def text_block(text: str) -> dict:
    return {"type": "text", "text": text}


def image_block(image_b64: str, *, media_type: str = "image/png") -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}}
