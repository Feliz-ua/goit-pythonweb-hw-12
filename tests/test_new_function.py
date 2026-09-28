from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.dependencies import require_admin
from app.models import User
from app.routes import auth


def make_user(*, user_id=1, email="user@example.com", role="user"):
    return User(
        id=user_id,
        username="Test User",
        email=email,
        password="old-hashed-password",
        avatar=None,
        confirmed=True,
        role=role,
    )


def test_cache_hit_returns_cached_user_with_role(monkeypatch):
    from app import dependencies

    cached_user = {
        "id": 1,
        "username": "Admin",
        "email": "admin@example.com",
        "password": "hashed-password",
        "avatar": None,
        "confirmed": True,
        "role": "admin",
    }
    db = MagicMock()

    monkeypatch.setattr(
        dependencies,
        "get_cached_user",
        lambda user_id: cached_user,
    )
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda token: {"sub": "1"},
    )

    result = dependencies.get_current_user("token", db)

    assert result.role == "admin"
    assert result.email == "admin@example.com"
    db.get.assert_not_called()


def test_cache_miss_reads_database_and_caches_user(monkeypatch):
    from app import dependencies

    user = make_user(role="user")
    db = MagicMock()
    db.get.return_value = user
    cache_user = MagicMock()

    monkeypatch.setattr(
        dependencies,
        "get_cached_user",
        lambda user_id: None,
    )
    monkeypatch.setattr(
        dependencies,
        "cache_user",
        cache_user,
    )
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda token: {"sub": "1"},
    )

    result = dependencies.get_current_user("token", db)

    assert result is user
    assert result.role == "user"
    db.get.assert_called_once_with(User, 1)
    cache_user.assert_called_once_with(user)


def test_admin_role_is_allowed():
    admin = make_user(role="admin")

    assert require_admin(admin) is admin


def test_regular_user_role_is_forbidden():
    user = make_user(role="user")

    with pytest.raises(HTTPException) as error:
        require_admin(user)

    assert error.value.status_code == 403
    assert error.value.detail == "Admin access required"


def test_password_reset_request_creates_token_and_sends_email():
    user = make_user(email="user@example.com")
    db = MagicMock()
    db.scalar.return_value = user

    with (
        patch.object(auth, "create_reset_token", return_value="reset-token") as create_token,
        patch.object(auth, "send_password_reset_email") as send_email,
    ):
        response = auth.request_password_reset(
            body=SimpleNamespace(email=user.email),
            db=db,
        )

    create_token.assert_called_once_with(user.id)
    send_email.assert_called_once_with(user.email, "reset-token")
    assert response["message"].startswith("If the email exists")


def test_password_reset_request_deletes_token_when_email_fails():
    user = make_user(email="user@example.com")
    db = MagicMock()
    db.scalar.return_value = user

    with (
        patch.object(auth, "create_reset_token", return_value="reset-token"),
        patch.object(
            auth,
            "send_password_reset_email",
            side_effect=RuntimeError("SMTP failure"),
        ),
        patch.object(auth, "delete_reset_token") as delete_token,
    ):
        with pytest.raises(HTTPException) as error:
            auth.request_password_reset(
                body=SimpleNamespace(email=user.email),
                db=db,
            )

    delete_token.assert_called_once_with("reset-token")
    assert error.value.status_code == 503


def test_password_reset_request_does_not_reveal_unknown_email():
    db = MagicMock()
    db.scalar.return_value = None

    with (
        patch.object(auth, "create_reset_token") as create_token,
        patch.object(auth, "send_password_reset_email") as send_email,
    ):
        response = auth.request_password_reset(
            body=SimpleNamespace(email="missing@example.com"),
            db=db,
        )

    create_token.assert_not_called()
    send_email.assert_not_called()
    assert response["message"].startswith("If the email exists")


def test_password_reset_confirm_changes_password(monkeypatch):
    user = make_user()
    db = MagicMock()
    db.get.return_value = user

    monkeypatch.setattr(auth, "consume_reset_token", lambda token: user.id)
    monkeypatch.setattr(auth, "hash_password", lambda password: "new-hash")

    response = auth.confirm_password_reset(
        body=SimpleNamespace(
            token="reset-token",
            new_password="new-password",
        ),
        db=db,
    )

    assert user.password == "new-hash"
    db.commit.assert_called_once()
    assert response["message"] == "Password has been reset successfully"


def test_password_reset_confirm_rejects_invalid_token(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(auth, "consume_reset_token", lambda token: None)

    with pytest.raises(HTTPException) as error:
        auth.confirm_password_reset(
            body=SimpleNamespace(
                token="invalid-token",
                new_password="new-password",
            ),
            db=db,
        )

    assert error.value.status_code == 400