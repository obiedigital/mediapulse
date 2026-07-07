"""Daily Brief archive — read-only list/detail. Generation is M4; this
router just exposes whatever `Brief` rows exist (empty archive until then).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...models import Brief, Tenant
from ...schemas import BriefOut
from ..deps import get_current_tenant, get_db

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.get("", response_model=list[BriefOut])
def list_briefs(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    briefs = (
        session.query(Brief)
        .filter_by(tenant_id=tenant.id)
        .order_by(Brief.period_end.desc())
        .limit(limit)
        .all()
    )
    return [
        BriefOut(
            id=b.id, brief_type=b.brief_type.value, status=b.status.value,
            period_start=b.period_start, period_end=b.period_end,
            generated_at=b.generated_at, published_at=b.published_at, sent_at=b.sent_at,
        )
        for b in briefs
    ]


@router.get("/{brief_id}", response_model=BriefOut)
def get_brief(
    brief_id: str, tenant: Tenant = Depends(get_current_tenant), session: Session = Depends(get_db)
):
    brief = session.query(Brief).filter_by(id=brief_id, tenant_id=tenant.id).one_or_none()
    if brief is None:
        raise HTTPException(404, "Brief not found")
    return BriefOut(
        id=brief.id, brief_type=brief.brief_type.value, status=brief.status.value,
        period_start=brief.period_start, period_end=brief.period_end,
        generated_at=brief.generated_at, published_at=brief.published_at, sent_at=brief.sent_at,
        html_content=brief.html_content,
    )
