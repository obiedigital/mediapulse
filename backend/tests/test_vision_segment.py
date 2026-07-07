import json
from pathlib import Path

import pytest

from mediapulse.ai.vision_segment import (
    VisionSegmentationError,
    render_page_png,
    segment_page_with_vision,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_PDF = FIXTURES / "daily_news_2026-06-10.pdf"

VALID_RESPONSE = json.dumps({
    "articles": [
        {
            "headline": "Media Raises Freedom Concerns",
            "byline": "By Staff Reporter",
            "body": "Full recovered article body from the scanned page.",
            "section": "News",
            "is_advert": False,
        }
    ]
})


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create_message(self, *, model, image_b64, prompt):
        self.calls += 1
        response = self._responses[min(self.calls - 1, len(self._responses) - 1)]
        if isinstance(response, Exception):
            raise response
        return response


def test_render_page_png_returns_valid_png_bytes():
    png_bytes = render_page_png(str(SAMPLE_PDF), 1)
    assert png_bytes.startswith(b"\x89PNG")


def test_segment_page_with_vision_parses_valid_response():
    client = FakeClient([VALID_RESPONSE])
    articles = segment_page_with_vision(str(SAMPLE_PDF), 1, client=client, max_retries=3, backoff_seconds=0)

    assert len(articles) == 1
    assert articles[0].headline == "Media Raises Freedom Concerns"
    assert articles[0].page == 1
    assert client.calls == 1


def test_segment_page_with_vision_strips_markdown_fence():
    fenced = f"```json\n{VALID_RESPONSE}\n```"
    client = FakeClient([fenced])
    articles = segment_page_with_vision(str(SAMPLE_PDF), 1, client=client, max_retries=3, backoff_seconds=0)
    assert articles[0].headline == "Media Raises Freedom Concerns"


def test_segment_page_with_vision_retries_on_bad_json_then_succeeds():
    client = FakeClient(["not json at all", VALID_RESPONSE])
    articles = segment_page_with_vision(str(SAMPLE_PDF), 1, client=client, max_retries=3, backoff_seconds=0)

    assert client.calls == 2
    assert articles[0].headline == "Media Raises Freedom Concerns"


def test_segment_page_with_vision_raises_clear_error_after_exhausting_retries():
    client = FakeClient(["garbage", "still garbage", "more garbage"])

    with pytest.raises(VisionSegmentationError, match="failed after 3 attempts"):
        segment_page_with_vision(str(SAMPLE_PDF), 1, client=client, max_retries=3, backoff_seconds=0)

    assert client.calls == 3


def test_segment_page_with_vision_retries_on_client_exception():
    client = FakeClient([ConnectionError("upstream timeout"), VALID_RESPONSE])
    articles = segment_page_with_vision(str(SAMPLE_PDF), 1, client=client, max_retries=3, backoff_seconds=0)
    assert articles[0].headline == "Media Raises Freedom Concerns"
