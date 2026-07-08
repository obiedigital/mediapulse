from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...ai.ask import AskError, ask_mediapulse
from ...models import Tenant
from ...schemas import AskCitationOut, AskRequest, AskResponse
from ..deps import get_ai_client, get_current_tenant, get_db

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("", response_model=AskResponse)
def ask(
    request: AskRequest,
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    client=Depends(get_ai_client),
):
    try:
        result = ask_mediapulse(session, tenant, request.question, client=client)
    except AskError as exc:
        raise HTTPException(502, f"Ask MediaPulse could not answer: {exc}") from exc

    return AskResponse(
        answer=result.answer,
        citations=[AskCitationOut(article_id=c.article_id, title=c.title) for c in result.citations],
    )
