from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...auth import create_access_token, verify_password
from ...models import User
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str | None
    role: str
    name: str


class CurrentUserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    tenant_id: str | None


@router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db)):
    user = session.query(User).filter_by(email=form_data.username).one_or_none()
    if user is None or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role.value)
    return LoginResponse(
        access_token=token, user_id=user.id, tenant_id=user.tenant_id,
        role=user.role.value, name=user.name,
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)):
    return CurrentUserResponse(
        user_id=current_user.id, email=current_user.email, name=current_user.name,
        role=current_user.role.value, tenant_id=current_user.tenant_id,
    )
