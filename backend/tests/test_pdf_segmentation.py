"""Proves the rebuilt print pipeline against the two synthetic sample PDFs
(standing in for the real Daily News 10-06-2026 and Botswana Gazette
06-05-2026 pages, which don't exist in this repo — see
tests/fixtures/build_sample_pdfs.py). Matches the exact expected-output
example from the product brief: real headlines, correct dates, no ad
fragments.
"""
import datetime as dt
from pathlib import Path

import fitz

from mediapulse.ingestion.pdf import segment_pdf

FIXTURES = Path(__file__).parent / "fixtures"


def test_daily_news_segments_into_real_articles_not_fragments():
    result = segment_pdf(FIXTURES / "daily_news_2026-06-10.pdf")

    headlines = {a.headline for a in result.articles if not a.is_advert}
    assert "Media Raises Freedom Concerns" in headlines
    assert "Batanani Walk Targets Child Protection" in headlines
    assert "Batswana Athletes Prepare for Regionals" in headlines
    assert result.masthead_date_raw == "Wednesday June 10, 2026"
    assert result.masthead_date == dt.date(2026, 6, 10)
    assert result.pages_needing_vision_fallback == []


def test_daily_news_filters_advertisement_out_of_editorial_headlines():
    result = segment_pdf(FIXTURES / "daily_news_2026-06-10.pdf")

    ads = [a for a in result.articles if a.is_advert]
    assert len(ads) == 1
    assert "ADVERTISEMENT" in ads[0].headline
    non_ads = [a for a in result.articles if not a.is_advert]
    assert all("ADVERTISEMENT" not in a.body for a in non_ads)


def test_daily_news_merges_continuation_across_pages():
    result = segment_pdf(FIXTURES / "daily_news_2026-06-10.pdf")

    article = next(a for a in result.articles if a.headline == "Media Raises Freedom Concerns")
    assert article.pages == [1, 2]
    assert "To Page" not in article.body
    assert "From Page" not in article.body
    assert "Editors Forum" in article.body
    assert "Civil society groups" in article.body  # the page-2 continuation text
    assert article.byline == "By Staff Reporter"


def test_daily_news_articles_have_no_headline_body_bleed():
    result = segment_pdf(FIXTURES / "daily_news_2026-06-10.pdf")
    for article in result.articles:
        assert article.headline not in article.body[len(article.headline):]


def test_gazette_segments_headline_and_rejects_notices_and_rate_tables():
    result = segment_pdf(FIXTURES / "gazette_2026-05-06.pdf")

    editorial = [a for a in result.articles if not a.is_advert]
    assert len(editorial) == 1
    assert editorial[0].headline == "Botswana bids for anti-money laundering academy"
    assert editorial[0].byline == "By Business Reporter"
    assert result.masthead_date_raw == "WEDNESDAY 06 MAY 2026"
    assert result.masthead_date == dt.date(2026, 5, 6)

    non_editorial = [a for a in result.articles if a.is_advert]
    non_editorial_text = " ".join(a.body for a in non_editorial)
    assert "INVITATION TO TENDER" in non_editorial_text
    assert "EXCHANGE RATES" in non_editorial_text


def test_gazette_notices_excluded_from_editorial_word_count():
    result = segment_pdf(FIXTURES / "gazette_2026-05-06.pdf")
    editorial_bodies = " ".join(a.body for a in result.articles if not a.is_advert)
    assert "tender" not in editorial_bodies.lower()
    assert "exchange rate" not in editorial_bodies.lower()


def test_degraded_page_with_no_headline_flagged_for_vision_fallback(tmp_path):
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_textbox(
        fitz.Rect(30, 30, 565, 60), "Wednesday June 10, 2026 | No. 83", fontsize=13, fontname="hebo"
    )
    page1.insert_textbox(fitz.Rect(40, 100, 290, 150), "Real Headline Here", fontsize=16, fontname="hebo")
    page1.insert_textbox(
        fitz.Rect(40, 160, 290, 300),
        "Body text long enough to count as real editorial content for this page.",
        fontsize=9,
    )
    page2 = doc.new_page()
    # Degraded scan: only tiny scattered OCR-noise fragments, no headline-sized
    # text and nothing resembling a real paragraph.
    page2.insert_textbox(fitz.Rect(40, 100, 120, 115), "ORANGE", fontsize=8)
    page2.insert_textbox(fitz.Rect(200, 300, 260, 315), "xyz", fontsize=8)

    pdf_path = tmp_path / "degraded.pdf"
    doc.save(str(pdf_path))
    doc.close()

    result = segment_pdf(pdf_path)

    assert result.pages_needing_vision_fallback == [2]
