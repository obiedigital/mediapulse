from __future__ import annotations

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class AskCitationOut(BaseModel):
    article_id: str
    title: str


class AskResponse(BaseModel):
    answer: str
    citations: list[AskCitationOut]
