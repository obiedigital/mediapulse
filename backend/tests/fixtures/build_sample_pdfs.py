"""Generates synthetic sample newspaper PDFs for testing the print
segmentation pipeline. No real Daily News / Botswana Gazette PDFs exist in
this repo, so these stand in for them: same masthead date conventions,
two-column layout, adverts/legal notices to filter, and a continuation
("To Page N" / "From Page N") spanning two pages — including the exact
headlines named as expected output in the product brief.

Run directly to (re)write the fixtures:
    python tests/fixtures/build_sample_pdfs.py
"""
from __future__ import annotations

from pathlib import Path

import fitz

FIXTURES_DIR = Path(__file__).parent

PAGE_WIDTH, PAGE_HEIGHT = fitz.paper_size("a4")
LEFT_COL = fitz.Rect(40, 100, 290, 780)
RIGHT_COL = fitz.Rect(305, 100, 555, 780)
MASTHEAD = fitz.Rect(30, 30, 565, 60)
FOLIO = fitz.Rect(30, 30, 300, 45)


def _insert(page, rect, text, *, fontsize, fontname="helv", align=fitz.TEXT_ALIGN_LEFT):
    rc = page.insert_textbox(rect, text, fontsize=fontsize, fontname=fontname, align=align)
    if rc < 0:
        raise ValueError(
            f"Text did not fit in rect {rect} at fontsize={fontsize}: {text[:60]!r} "
            f"(overflow={-rc:.1f}pt) — enlarge the rect."
        )


def build_daily_news_pdf(path: Path) -> None:
    doc = fitz.open()

    page1 = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    _insert(page1, MASTHEAD, "Wednesday June 10, 2026 | No. 83", fontsize=13, fontname="hebo")

    left = fitz.Rect(LEFT_COL.x0, 95, LEFT_COL.x1, 150)
    _insert(page1, left, "Media Raises Freedom Concerns", fontsize=16, fontname="hebo")
    left_byline = fitz.Rect(LEFT_COL.x0, 152, LEFT_COL.x1, 168)
    _insert(page1, left_byline, "By Staff Reporter", fontsize=9, fontname="heit")
    left_body = fitz.Rect(LEFT_COL.x0, 172, LEFT_COL.x1, 400)
    _insert(
        page1, left_body,
        "Media practitioners in Botswana have raised concerns over proposed "
        "amendments that could restrict access to public information. "
        "Editors say the changes would make it harder to hold public "
        "officials accountable ahead of the next reporting cycle. The "
        "Botswana Editors Forum said it had written to the Ministry "
        "requesting urgent consultations on the matter. To Page 2",
        fontsize=9,
    )

    right = fitz.Rect(RIGHT_COL.x0, 95, RIGHT_COL.x1, 150)
    _insert(page1, right, "Batanani Walk Targets Child Protection", fontsize=16, fontname="hebo")
    right_byline = fitz.Rect(RIGHT_COL.x0, 152, RIGHT_COL.x1, 168)
    _insert(page1, right_byline, "By Community Correspondent", fontsize=9, fontname="heit")
    right_body = fitz.Rect(RIGHT_COL.x0, 172, RIGHT_COL.x1, 400)
    _insert(
        page1, right_body,
        "Hundreds of residents took part in the annual Batanani Walk over "
        "the weekend, raising awareness about child protection services "
        "available in the district. Organisers said proceeds from the "
        "walk would go towards a local shelter for vulnerable children.",
        fontsize=9,
    )

    ad_rect = fitz.Rect(LEFT_COL.x0, 600, RIGHT_COL.x1, 700)
    _insert(
        page1, ad_rect,
        "ADVERTISEMENT\nBest prices on used cars! Call 71234567 today for a "
        "free quote on your next vehicle purchase.",
        fontsize=10,
    )

    page2 = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    _insert(page2, FOLIO, "Daily News - Page 2", fontsize=8)

    left2_body = fitz.Rect(LEFT_COL.x0, 100, LEFT_COL.x1, 250)
    _insert(
        page2, left2_body,
        "From Page 1: The Ministry has not yet responded to the Forum's "
        "request. Civil society groups have echoed the call for "
        "transparency, warning that reduced access to information could "
        "undermine oversight of public spending.",
        fontsize=9,
    )

    right2 = fitz.Rect(RIGHT_COL.x0, 95, RIGHT_COL.x1, 150)
    _insert(page2, right2, "Batswana Athletes Prepare for Regionals", fontsize=16, fontname="hebo")
    right2_byline = fitz.Rect(RIGHT_COL.x0, 152, RIGHT_COL.x1, 168)
    _insert(page2, right2_byline, "By Sports Desk", fontsize=9, fontname="heit")
    right2_body = fitz.Rect(RIGHT_COL.x0, 172, RIGHT_COL.x1, 350)
    _insert(
        page2, right2_body,
        "The national athletics team departs this weekend for the regional "
        "championships, with officials expressing confidence in a strong "
        "medal haul across the sprint and field events.",
        fontsize=9,
    )

    doc.save(str(path))
    doc.close()


def build_gazette_pdf(path: Path) -> None:
    doc = fitz.open()
    page1 = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    _insert(page1, MASTHEAD, "WEDNESDAY 06 MAY 2026 | Botswana Gazette", fontsize=13, fontname="hebo")

    left = fitz.Rect(LEFT_COL.x0, 95, LEFT_COL.x1, 150)
    _insert(page1, left, "Botswana bids for anti-money laundering academy", fontsize=16, fontname="hebo")
    left_byline = fitz.Rect(LEFT_COL.x0, 152, LEFT_COL.x1, 168)
    _insert(page1, left_byline, "By Business Reporter", fontsize=9, fontname="heit")
    left_body = fitz.Rect(LEFT_COL.x0, 172, LEFT_COL.x1, 400)
    _insert(
        page1, left_body,
        "Government has formally submitted a bid to host a regional "
        "anti-money laundering training academy, positioning Gaborone as "
        "a financial compliance hub for the sub-region. Officials said "
        "the academy would train investigators from across the SADC "
        "region in tracing illicit financial flows.",
        fontsize=9,
    )

    notice_rect = fitz.Rect(RIGHT_COL.x0, 100, RIGHT_COL.x1, 260)
    _insert(
        page1, notice_rect,
        "INVITATION TO TENDER\nSealed bids are invited for the supply and "
        "delivery of office furniture to BOCRA regional offices. Closing "
        "date for submissions is 30 June 2026.",
        fontsize=9,
    )

    rates_rect = fitz.Rect(RIGHT_COL.x0, 280, RIGHT_COL.x1, 420)
    _insert(
        page1, rates_rect,
        "EXCHANGE RATES\nUSD/BWP 13.45\nZAR/BWP 0.75\nGBP/BWP 17.02\n"
        "EUR/BWP 14.60",
        fontsize=9,
    )

    doc.save(str(path))
    doc.close()


if __name__ == "__main__":
    build_daily_news_pdf(FIXTURES_DIR / "daily_news_2026-06-10.pdf")
    build_gazette_pdf(FIXTURES_DIR / "gazette_2026-05-06.pdf")
    print("Wrote sample PDFs to", FIXTURES_DIR)
