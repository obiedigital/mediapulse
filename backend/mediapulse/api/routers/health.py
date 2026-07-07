from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from ...models import Source, Tenant, Topic, UserRole
from ...schemas import SourceHealthOut
from ..deps import get_current_tenant, get_db, require_roles

router = APIRouter(tags=["ops"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/admin/sources", response_model=list[SourceHealthOut])
def source_health(
    tenant: Tenant = Depends(get_current_tenant),
    session: Session = Depends(get_db),
    _admin=Depends(require_roles(UserRole.platform_admin, UserRole.admin)),
):
    sources = (
        session.query(Source)
        .join(Source.topic)
        .options(joinedload(Source.topic))
        .filter(Topic.tenant_id == tenant.id)
        .all()
    )
    return [
        SourceHealthOut(
            id=s.id, name=s.name, type=s.type.value, topic_label=s.topic.label,
            is_active=s.is_active, last_fetched_at=s.last_fetched_at,
            last_success_at=s.last_success_at, consecutive_error_count=s.consecutive_error_count,
            last_error=s.last_error,
        )
        for s in sources
    ]
