import jwt
import pytest

from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password = "StrongPassword123"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("WrongPassword", hashed_password)


def test_create_and_decode_access_token():
    token = create_access_token("42")

    payload = decode_access_token(token)

    assert payload["sub"] == "42"


def test_decode_invalid_access_token():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("invalid.token.value")
