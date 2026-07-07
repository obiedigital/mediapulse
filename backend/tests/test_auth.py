import pytest

from mediapulse.auth import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_hash_password_uses_unique_salt():
    a = hash_password("same-password")
    b = hash_password("same-password")
    assert a != b


def test_verify_password_rejects_garbage_hash():
    assert not verify_password("anything", "not-a-real-hash")


def test_access_token_roundtrip():
    token = create_access_token(user_id="user-1", tenant_id="tenant-1", role="analyst")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["role"] == "analyst"


def test_access_token_rejects_tampered_token():
    token = create_access_token(user_id="user-1", tenant_id="tenant-1", role="analyst")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_access_token_expires():
    token = create_access_token(user_id="user-1", tenant_id="tenant-1", role="analyst", expires_minutes=-1)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
