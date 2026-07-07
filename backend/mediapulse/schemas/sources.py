from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class SourceHealthOut(BaseModel):
    id: str
    name: str
    type: str
    topic_label: str
    is_active: bool
    last_fetched_at: dt.datetime | None
    last_success_at: dt.datetime | None
    consecutive_error_count: int
    last_error: str | None
