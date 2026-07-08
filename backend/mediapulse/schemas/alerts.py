from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: str
    alert_type: str
    message: str
    article_id: str | None
    created_at: dt.datetime
    sent_at: dt.datetime | None
