"""Shared helper for stripping a ```json fence``` Claude sometimes wraps
JSON output in, despite being asked for a bare object. Used by both the
vision segmentation and classification call sites.
"""
from __future__ import annotations

import re

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


def extract_json_object(text: str) -> str:
    fenced = _FENCE_RE.search(text)
    return fenced.group(1) if fenced else text
