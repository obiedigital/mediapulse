"""Shared non-editorial content detection — used by both the legacy
importer and the print PDF segmentation pipeline so "what counts as an
advert/notice" is defined exactly once.
"""
from __future__ import annotations

NON_EDITORIAL_KEYWORDS = (
    "invitation to tender",
    "tender notice",
    "legal notice",
    "notice of intention",
    "public notice",
    "classifieds",
    "rate table",
    "exchange rates",
    "advertisement",
    "advertorial",
)


def looks_non_editorial(title: str, body: str, *, scan_chars: int = 500) -> bool:
    haystack = f"{title}\n{body[:scan_chars]}".lower()
    return any(keyword in haystack for keyword in NON_EDITORIAL_KEYWORDS)
