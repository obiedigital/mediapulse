import datetime as dt

from mediapulse.ingestion.dates import (
    DateConfidence,
    extract_masthead_date,
    is_plausible_publication_date,
    resolve_published_at,
)


def test_extracts_weekday_month_day_year_masthead():
    text = "Wednesday June 10, 2026 | No. 83\nSome front page story text..."
    parsed = extract_masthead_date(text)
    assert parsed.value == dt.date(2026, 6, 10)
    assert parsed.confidence == DateConfidence.HIGH


def test_extracts_weekday_day_month_year_masthead():
    text = "WEDNESDAY 06 MAY 2026\nBotswana Gazette weekly edition..."
    parsed = extract_masthead_date(text)
    assert parsed.value == dt.date(2026, 5, 6)
    assert parsed.confidence == DateConfidence.HIGH


def test_rejects_weekday_checksum_mismatch():
    # June 10 2026 is a Wednesday, not a Monday — OCR noise should not be trusted.
    text = "Monday June 10, 2026\nBody text"
    parsed = extract_masthead_date(text)
    assert parsed.value is None
    assert parsed.confidence == DateConfidence.LOW


def test_bare_numeric_date_is_medium_confidence():
    text = "10 June 2026\nBody text with no weekday given"
    parsed = extract_masthead_date(text)
    assert parsed.value == dt.date(2026, 6, 10)
    assert parsed.confidence == DateConfidence.MEDIUM


def test_no_date_found_returns_low_confidence():
    parsed = extract_masthead_date("Just some article body with no date at all.")
    assert parsed.value is None
    assert parsed.confidence == DateConfidence.LOW


def test_implausible_year_rejected():
    fetched = dt.date(2026, 6, 11)
    assert not is_plausible_publication_date(dt.date(1780, 1, 1), fetched_at=fetched)


def test_far_future_date_rejected():
    fetched = dt.date(2026, 6, 11)
    assert not is_plausible_publication_date(dt.date(2027, 1, 1), fetched_at=fetched)


def test_resolve_recovers_masthead_date_over_garbage_legacy_value():
    fetched_at = dt.datetime(2026, 6, 11, 8, 0, tzinfo=dt.timezone.utc)
    raw_text = "Wednesday June 10, 2026 | No. 83\nMedia Raises Freedom Concerns\n..."
    # legacy garbage: month=46, day=43 is not parseable at all
    published, raw_match, confidence = resolve_published_at(
        raw_text, fetched_at=fetched_at, existing_published_at=None
    )
    assert published.date() == dt.date(2026, 6, 10)
    assert raw_match is not None
    assert confidence == DateConfidence.HIGH


def test_resolve_falls_back_to_fetched_at_when_nothing_found():
    fetched_at = dt.datetime(2026, 6, 11, 8, 0, tzinfo=dt.timezone.utc)
    published, raw_match, confidence = resolve_published_at(
        "no usable date here", fetched_at=fetched_at, existing_published_at=None
    )
    assert published == fetched_at
    assert confidence == DateConfidence.LOW


def test_resolve_keeps_plausible_existing_web_published_at():
    fetched_at = dt.datetime(2026, 6, 11, 9, 0, tzinfo=dt.timezone.utc)
    existing = dt.datetime(2026, 6, 9, 14, 30, tzinfo=dt.timezone.utc)
    published, _, confidence = resolve_published_at(
        "Web article body, no masthead date pattern here.",
        fetched_at=fetched_at,
        existing_published_at=existing,
    )
    assert published == existing
    assert confidence == DateConfidence.MEDIUM
