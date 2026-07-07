"""Layout-aware print PDF article segmentation.

Replaces the legacy pipeline that OCR'd a page into dozens of
headline-less fragments (defect #3). Uses PyMuPDF's block/coordinate
output plus a heading font-size heuristic to group text into real
articles: detect columns from block x-coordinates, classify each block
(masthead / headline / byline / body / advert-or-notice), walk each
column in reading order building one article per headline, merge
"From Page N" / "To Page N" continuations across pages, and drop
adverts/tenders/legal notices/rate tables from the editorial count
(they're still returned, flagged `is_advert=True`, for a tenant that opts
into brand-in-advert tracking).

A page whose blocks don't cleanly resolve (e.g. a heavily degraded scan
with no detectable headline-sized text) is reported with
`needs_vision_fallback=True` so the caller can send it to
`ai.vision_segment` instead of guessing.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF

from .dates import extract_masthead_date
from .filters import looks_non_editorial

HEADLINE_FONT_SIZE_THRESHOLD = 13.0
MASTHEAD_Y_LIMIT = 80.0
COLUMN_GAP_TOLERANCE = 20.0

_BYLINE_RE = re.compile(r"^\s*by\s+[A-Z][\w .,'-]{2,60}$", re.IGNORECASE)
_TO_PAGE_RE = re.compile(r"\b(?:to|continued\s+on)\s+page\s+(\d+)\b", re.IGNORECASE)
_FROM_PAGE_RE = re.compile(r"^\s*from\s+page\s+(\d+)\b[:.]?\s*", re.IGNORECASE)


@dataclass
class SegmentedArticle:
    headline: str
    body: str
    byline: str | None = None
    pages: list[int] = field(default_factory=list)
    is_advert: bool = False


@dataclass
class PdfSegmentationResult:
    articles: list[SegmentedArticle]
    masthead_date_raw: str | None
    masthead_date: dt.date | None
    pages_needing_vision_fallback: list[int]


@dataclass
class _Block:
    text: str
    x0: float
    y0: float
    page: int
    max_font_size: float


def _extract_blocks(page, page_number: int) -> list[_Block]:
    raw = page.get_text("dict")
    blocks: list[_Block] = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines_text = []
        max_size = 0.0
        for line in block.get("lines", []):
            span_text = "".join(span["text"] for span in line.get("spans", []))
            lines_text.append(span_text)
            for span in line.get("spans", []):
                max_size = max(max_size, span.get("size", 0.0))
        # Lines within one block are just word-wrap, not paragraph breaks —
        # join with a space so "Media Raises Freedom\nConcerns" (a wrap
        # mid-headline) reads as one clean line, not two glued words.
        text = " ".join(t.strip() for t in lines_text if t.strip())
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        x0, y0 = block["bbox"][0], block["bbox"][1]
        blocks.append(_Block(text=text, x0=x0, y0=y0, page=page_number, max_font_size=max_size))
    return blocks


def _cluster_columns(blocks: list[_Block], tolerance: float = COLUMN_GAP_TOLERANCE) -> dict[int, int]:
    """Map each distinct x0 to a column index by grouping nearby x0s."""
    xs = sorted({round(b.x0) for b in blocks})
    clusters: list[list[float]] = []
    for x in xs:
        if clusters and x - clusters[-1][-1] <= tolerance:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    x_to_column = {}
    for idx, cluster in enumerate(clusters):
        for x in cluster:
            x_to_column[x] = idx
    return x_to_column


class _BlockKind:
    MASTHEAD = "masthead"
    AD_OR_NOTICE = "ad_or_notice"
    HEADLINE = "headline"
    BYLINE = "byline"
    BODY = "body"
    FOLIO = "folio"  # page number / running head, ignored


def _classify(block: _Block, *, is_first_page: bool) -> str:
    first_line = block.text.strip().splitlines()[0] if block.text.strip() else ""

    if is_first_page and block.y0 < MASTHEAD_Y_LIMIT and extract_masthead_date(block.text).value:
        return _BlockKind.MASTHEAD
    if looks_non_editorial(first_line, block.text):
        return _BlockKind.AD_OR_NOTICE
    if len(block.text.strip()) < 40 and block.y0 < MASTHEAD_Y_LIMIT:
        return _BlockKind.FOLIO
    if block.max_font_size >= HEADLINE_FONT_SIZE_THRESHOLD:
        return _BlockKind.HEADLINE
    if _BYLINE_RE.match(first_line):
        return _BlockKind.BYLINE
    return _BlockKind.BODY


def segment_pdf(path: str | Path) -> PdfSegmentationResult:
    doc = fitz.open(str(path))
    masthead_date_raw: str | None = None
    masthead_date: dt.date | None = None
    pages_needing_vision_fallback: list[int] = []

    all_blocks: list[_Block] = []
    for page_index, page in enumerate(doc, start=1):
        all_blocks.extend(_extract_blocks(page, page_index))

    x_to_column = _cluster_columns(all_blocks)

    articles: list[SegmentedArticle] = []
    current: SegmentedArticle | None = None
    # target_page -> list of articles awaiting continuation text on that page
    pending_continuations: dict[int, list[SegmentedArticle]] = {}

    pages = sorted({b.page for b in all_blocks})
    for page_number in pages:
        page_blocks = [b for b in all_blocks if b.page == page_number]
        page_blocks.sort(key=lambda b: (x_to_column.get(round(b.x0), 0), b.y0))

        page_had_headline = False
        current = None  # articles don't silently carry across a headline-less page gap

        for block in page_blocks:
            kind = _classify(block, is_first_page=(page_number == pages[0]))

            if kind == _BlockKind.MASTHEAD:
                if masthead_date_raw is None:
                    parsed_masthead = extract_masthead_date(block.text)
                    masthead_date_raw = parsed_masthead.raw_match or block.text.strip()
                    masthead_date = parsed_masthead.value
                continue
            if kind == _BlockKind.FOLIO:
                continue
            if kind == _BlockKind.AD_OR_NOTICE:
                articles.append(
                    SegmentedArticle(
                        headline=block.text.strip().splitlines()[0][:120],
                        body=block.text,
                        pages=[page_number],
                        is_advert=True,
                    )
                )
                continue

            text = block.text
            from_match = _FROM_PAGE_RE.match(text)
            if from_match and not page_had_headline:
                source_target = page_number
                waiting = pending_continuations.get(source_target, [])
                if waiting:
                    continuing_article = waiting.pop(0)
                    continuing_article.body += "\n" + _FROM_PAGE_RE.sub("", text, count=1)
                    if page_number not in continuing_article.pages:
                        continuing_article.pages.append(page_number)
                    current = continuing_article
                    continue
                # No pending continuation registered — fall through and treat
                # as an orphan body block rather than dropping the text.

            if kind == _BlockKind.HEADLINE:
                page_had_headline = True
                current = SegmentedArticle(headline=text.strip(), body="", pages=[page_number])
                articles.append(current)
                continue

            if kind == _BlockKind.BYLINE:
                if current is not None:
                    current.byline = text.strip()
                continue

            # BODY
            to_match = _TO_PAGE_RE.search(text)
            clean_text = _TO_PAGE_RE.sub("", text).strip()
            if current is not None:
                current.body = f"{current.body}\n{clean_text}".strip()
                if page_number not in current.pages:
                    current.pages.append(page_number)
            else:
                # A body block with no headline and no continuation match —
                # keep it as a standalone item rather than discarding text,
                # but it's a strong signal this page needs a closer look.
                current = SegmentedArticle(headline=clean_text[:80] or "(untitled)", body=clean_text, pages=[page_number])
                articles.append(current)

            if to_match and current is not None:
                target_page = int(to_match.group(1))
                pending_continuations.setdefault(target_page, []).append(current)

    # Flag pages where no headline-sized block was found at all as candidates
    # for the vision fallback (heuristic segmentation likely missed structure).
    headline_pages = {
        b.page for b in all_blocks if b.max_font_size >= HEADLINE_FONT_SIZE_THRESHOLD
    }
    for page_number in pages:
        page_has_only_folio_or_nothing = page_number not in headline_pages and not any(
            _FROM_PAGE_RE.match(b.text.strip()) for b in all_blocks if b.page == page_number
        )
        if page_has_only_folio_or_nothing and page_number != pages[0]:
            # First page always carries the masthead; subsequent headline-free
            # pages are suspicious unless explicitly a continuation page.
            has_real_body = any(
                len(b.text.strip()) >= 40 for b in all_blocks if b.page == page_number
            )
            if not has_real_body:
                pages_needing_vision_fallback.append(page_number)

    editorial_and_ads = [a for a in articles if a.body.strip() or a.is_advert]
    return PdfSegmentationResult(
        articles=editorial_and_ads,
        masthead_date_raw=masthead_date_raw,
        masthead_date=masthead_date,
        pages_needing_vision_fallback=pages_needing_vision_fallback,
    )
