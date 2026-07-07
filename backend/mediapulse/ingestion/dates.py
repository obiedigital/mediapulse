"""Publication-date recovery for print PDF ingestion.

Legacy bug (M0 defect #2): every print item's `published_at` was written as
either the *fetch* date or outright garbage (e.g. "1780-46-43" — an invalid
month/day pair that presumably fell out of a broken strptime/offset
calculation). This module derives the true publication date from the
masthead/page-header text instead of trusting whatever the ingestor wrote,
and refuses to silently accept a value it cannot validate.

Two independent signals are used together, since Botswana print mastheads
commonly render as either:
  "Wednesday June 10, 2026 | No. 83"    (weekday, Month DD, YYYY)
  "WEDNESDAY 06 MAY 2026"               (weekday, DD Month YYYY)

The weekday name is treated as a checksum: if "Wednesday" is present, the
computed date must actually fall on a Wednesday, or the match is discarded
as OCR noise rather than accepted at low confidence.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from enum import Enum

_MONTHS = {
    name.lower(): i
    for i, name in enumerate(
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        start=1,
    )
}
# 3-letter abbreviations
_MONTHS.update({name[:3].lower(): num for name, num in list(_MONTHS.items())})

_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

_MONTH_ALT = "|".join(sorted(_MONTHS.keys(), key=len, reverse=True))
_WEEKDAY_ALT = "|".join(_WEEKDAYS.keys())

# "Wednesday June 10, 2026" / "Wednesday, June 10 2026"
_PATTERN_WEEKDAY_MONTH_DAY_YEAR = re.compile(
    rf"\b(?P<weekday>{_WEEKDAY_ALT})\b[,\s]+(?P<month>{_MONTH_ALT})\.?\s+"
    rf"(?P<day>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<year>\d{{4}})",
    re.IGNORECASE,
)
# "WEDNESDAY 06 MAY 2026"
_PATTERN_WEEKDAY_DAY_MONTH_YEAR = re.compile(
    rf"\b(?P<weekday>{_WEEKDAY_ALT})\b\s+(?P<day>\d{{1,2}})\s+"
    rf"(?P<month>{_MONTH_ALT})\.?\s+(?P<year>\d{{4}})",
    re.IGNORECASE,
)
# Bare "10 June 2026" / "June 10, 2026" without a weekday — lower confidence,
# no checksum available.
_PATTERN_DAY_MONTH_YEAR = re.compile(
    rf"\b(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<month>{_MONTH_ALT})\.?\s+(?P<year>\d{{4}})",
    re.IGNORECASE,
)
_PATTERN_MONTH_DAY_YEAR = re.compile(
    rf"\b(?P<month>{_MONTH_ALT})\.?\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<year>\d{{4}})",
    re.IGNORECASE,
)


class DateConfidence(str, Enum):
    HIGH = "high"  # weekday checksum matched
    MEDIUM = "medium"  # numeric date found, no weekday to verify against
    LOW = "low"  # nothing usable found; caller fell back to fetch date
    UNKNOWN = "unknown"


@dataclass
class ParsedDate:
    value: dt.date | None
    raw_match: str | None
    confidence: DateConfidence


def _build_date(year: str, month: str, day: str) -> dt.date | None:
    try:
        month_num = _MONTHS[month.lower()]
        return dt.date(int(year), month_num, int(day))
    except (KeyError, ValueError):
        return None


def extract_masthead_date(text: str, *, max_scan_chars: int = 4000) -> ParsedDate:
    """Scan the start of a page/article's raw text for a masthead date.

    Only the first `max_scan_chars` are scanned — mastheads live at the top
    of the page, and scanning the full body risks matching an unrelated
    date mentioned mid-article (e.g. a quote referencing a past event).
    """
    head = text[:max_scan_chars]

    weekday_present_but_unverified = False
    for pattern in (_PATTERN_WEEKDAY_MONTH_DAY_YEAR, _PATTERN_WEEKDAY_DAY_MONTH_YEAR):
        match = pattern.search(head)
        if not match:
            continue
        candidate = _build_date(match["year"], match["month"], match["day"])
        if candidate is None:
            weekday_present_but_unverified = True
            continue
        expected_weekday = _WEEKDAYS[match["weekday"].lower()]
        if candidate.weekday() == expected_weekday:
            return ParsedDate(candidate, match.group(0), DateConfidence.HIGH)
        # Weekday checksum failed — likely OCR noise mangling the day/month.
        # Don't fall through to a bare numeric match on the same corrupted
        # text; treat the whole masthead date as unreliable instead.
        weekday_present_but_unverified = True

    if weekday_present_but_unverified:
        return ParsedDate(None, None, DateConfidence.LOW)

    for pattern in (_PATTERN_DAY_MONTH_YEAR, _PATTERN_MONTH_DAY_YEAR):
        match = pattern.search(head)
        if not match:
            continue
        candidate = _build_date(match["year"], match["month"], match["day"])
        if candidate is not None:
            return ParsedDate(candidate, match.group(0), DateConfidence.MEDIUM)

    return ParsedDate(None, None, DateConfidence.LOW)


def is_plausible_publication_date(
    candidate: dt.date, *, fetched_at: dt.date, min_year: int = 2015, future_grace_days: int = 3
) -> bool:
    """Reject dates outside a sane window even if they parsed successfully —
    this is what would have caught the legacy "1780-46-43" class of bug
    (which parsed to *nothing*, but a similarly malformed "17-08-04" could
    parse to a valid but absurd date)."""
    if candidate.year < min_year:
        return False
    if candidate > fetched_at + dt.timedelta(days=future_grace_days):
        return False
    if candidate < fetched_at - dt.timedelta(days=365 * 3):
        return False
    return True


def resolve_published_at(
    raw_text: str,
    *,
    fetched_at: dt.datetime,
    existing_published_at: dt.datetime | None,
) -> tuple[dt.datetime, str | None, DateConfidence]:
    """Best-effort recovery of the true publication date for one legacy row.

    Returns (published_at, raw_matched_string, confidence). Falls back to
    fetched_at with LOW confidence only when no masthead date can be found
    or validated — callers should flag LOW-confidence rows for human review
    rather than trusting them silently.
    """
    parsed = extract_masthead_date(raw_text)
    if parsed.value is not None and is_plausible_publication_date(
        parsed.value, fetched_at=fetched_at.date()
    ):
        return (
            dt.datetime.combine(parsed.value, dt.time.min, tzinfo=fetched_at.tzinfo),
            parsed.raw_match,
            parsed.confidence,
        )

    # The existing value might already be correct (web-sourced articles with
    # a real feed-provided published_at) — keep it if it's plausible and
    # differs meaningfully from the fetch date (i.e. wasn't just copied).
    if existing_published_at is not None:
        delta = abs((existing_published_at - fetched_at).total_seconds())
        if delta > 60 and is_plausible_publication_date(
            existing_published_at.date(), fetched_at=fetched_at.date()
        ):
            return existing_published_at, None, DateConfidence.MEDIUM

    return fetched_at, None, DateConfidence.LOW
