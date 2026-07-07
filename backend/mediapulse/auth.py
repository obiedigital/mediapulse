"""Password hashing and JWT issuance/verification.

Uses stdlib `hashlib.pbkdf2_hmac` rather than pulling in bcrypt/argon2 — no
native extension to build in constrained environments, and PBKDF2-SHA256
with a high iteration count is still an acceptable KDF for this stage of
the product. Revisit if a real security review calls for argon2id.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import secrets

import jwt

from .config import get_settings

_PBKDF2_ITERATIONS = 260_000
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        algorithm, iterations, salt, expected_hex = hashed.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return secrets.compare_digest(digest.hex(), expected_hex)
    except (ValueError, AttributeError):
        return False


def create_access_token(
    *, user_id: str, tenant_id: str | None, role: str, expires_minutes: int = 60 * 12
) -> str:
    settings = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "iat": now,
        "exp": now + dt.timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
