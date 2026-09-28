from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from app.dependencies import get_current_user
from app.models import User


def make_user(
    *,
    user_id: int = 1,
    username: str = "john",
    email: str = "john@example.com",
    role: str = "user",
) -> User:
    return User(
        id=user_id,
        username=username,
        email=email,
        password="hashed-password",
        avatar=None,
        confirmed=True,
        role=role,
    )


def test_get_current_user_cache_miss(monkeypatch):
    db = MagicMock()
    user = make_user()

    monkeypatch.setattr(
        "app.dependencies.get_cached_user",
        lambda user_id: None,
    )
    monkeypatch.setattr(
        "app.dependencies.cache_user",
        lambda cached_user: None,
    )

    db.get.return_value = user

    with patch(
        "app.dependencies.decode_access_token",
        return_value={"sub": "1"},
    ):
        result = get_current_user("valid-token", db)

    assert result is user
    db.get.assert_called_once_with(User, 1)


def test_get_current_user_cache_hit(monkeypatch):
    db = MagicMock()

    cached_user = {
        "id": 1,
        "username": "john",
        "email": "john@example.com",
        "password": "hashed-password",
        "avatar": None,
        "confirmed": True,
        "role": "admin",
    }

    monkeypatch.setattr(
        "app.dependencies.get_cached_user",
        lambda user_id: cached_user,
    )

    with patch(
        "app.dependencies.decode_access_token",
        return_value={"sub": "1"},
    ):
        result = get_current_user("valid-token", db)

    assert result.id == 1
    assert result.email == "john@example.com"
    assert result.role == "admin"
    db.get.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"sub": None},
        {"sub": "not-an-integer"},
    ],
)
def test_get_current_user_invalid_subject(payload):
    db = MagicMock()

    with (
        patch(
            "app.dependencies.decode_access_token",
            return_value=payload,
        ),
        pytest.raises(HTTPException) as error,
    ):
        get_current_user("invalid-token", db)

    assert error.value.status_code == 401
    assert error.value.detail == "Could not validate credentials"
    db.get.assert_not_called()


def test_get_current_user_invalid_jwt():
    db = MagicMock()

    with (
        patch(
            "app.dependencies.decode_access_token",
            side_effect=jwt.InvalidTokenError,
        ),
        pytest.raises(HTTPException) as error,
    ):
        get_current_user("invalid-token", db)

    assert error.value.status_code == 401
    assert error.value.detail == "Could not validate credentials"
    db.get.assert_not_called()


def test_get_current_user_user_not_found(monkeypatch):
    db = MagicMock()
    db.get.return_value = None

    monkeypatch.setattr(
        "app.dependencies.get_cached_user",
        lambda user_id: None,
    )

    with (
        patch(
            "app.dependencies.decode_access_token",
            return_value={"sub": "1"},
        ),
        pytest.raises(HTTPException) as error,
    ):
        get_current_user("valid-token", db)

    assert error.value.status_code == 401
    assert error.value.detail == "Could not validate credentials"
    db.get.assert_called_once_with(User, 1)