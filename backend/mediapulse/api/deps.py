"""Shared FastAPI dependencies: DB session, current user, tenant scoping,
and role gating.

Tenant scoping rule: a tenant-scoped user (admin/analyst/client_viewer)
always sees their own tenant's data — the `tenant` query param, if given,
must match or the request is rejected. A `platform_admin` (no tenant_id)
must pass `?tenant=<slug>` to select which tenant's data to view, since
they aren't bound to one.
"""
from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..auth import InvalidTokenError, decode_access_token
from ..db import SessionLocal
from ..models import Tenant, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    token: str | None = Depends(oauth2_scheme), session: Session = Depends(get_db)
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise unauthorized
    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise unauthorized from exc

    user = session.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise unauthorized
    return user


def get_current_tenant(
    current_user: User = Depends(get_current_user),
    tenant: str | None = Query(None, description="Tenant slug (platform_admin only)"),
    session: Session = Depends(get_db),
) -> Tenant:
    if current_user.tenant_id is not None:
        row = session.get(Tenant, current_user.tenant_id)
        if tenant and row is not None and tenant != row.slug:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot access another tenant's data")
        return row

    if not tenant:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "?tenant=<slug> is required for platform_admin users")
    row = session.query(Tenant).filter_by(slug=tenant).one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No tenant {tenant!r}")
    return row


def require_roles(*roles: UserRole):
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return current_user

    return _check


def get_ai_client():
    """Returns None by default, letting AI call sites fall back to the real
    `AnthropicClientAdapter`. Exists as a dependency (rather than a plain
    function call) purely so tests can override it with a fake client —
    see tests/api/conftest.py."""
    return None
