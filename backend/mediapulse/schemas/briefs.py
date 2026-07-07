from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class BriefOut(BaseModel):
    id: str
    brief_type: str
    status: str
    period_start: dt.datetime
    period_end: dt.datetime
    generated_at: dt.datetime | None
    published_at: dt.datetime | None
    sent_at: dt.datetime | None
    html_content: str | None = None
