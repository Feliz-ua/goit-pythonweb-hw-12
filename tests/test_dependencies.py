from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from app.dependencies import get_current_user
from app.models import User


def test_get_current_user_success():
    db = MagicMock()

    user = User(
        id=1,
        username="john",
        email="john@example.com",
        password="hashed-password",
        avatar=None,
        confirmed=True,
    )

    db.get.return_value = user

    with patch(
        "app.dependencies.decode_access_token",
        return_value={"sub": "1"},
    ):
        result = get_current_user("valid-token", db)

    assert result is user
    db.get.assert_called_once_with(User, 1)


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


def test_get_current_user_user_not_found():
    db = MagicMock()
    db.get.return_value = None

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
