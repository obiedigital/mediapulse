from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...models import Alert, Tenant
from ...schemas import AlertOut
from ..deps import get_current_tenant, get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    rows = (
        session.query(Alert)
        .filter_by(tenant_id=tenant.id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        AlertOut(
            id=a.id, alert_type=a.alert_type.value, message=a.message,
            article_id=a.article_id, created_at=a.created_at, sent_at=a.sent_at,
        )
        for a in rows
    ]
