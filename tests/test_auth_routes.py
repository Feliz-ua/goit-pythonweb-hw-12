from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_healthcheck(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Contacts API is running",
    }


@patch("app.routes.auth.send_verification_email")
@patch("app.routes.auth.create_verification_token")
def test_register_success(
    mock_create_token,
    mock_send_email,
    client,
    db,
):
    db.scalar.return_value = None
    mock_create_token.return_value = "verification-token"

    def refresh_user(user):
        user.id = 1

    db.refresh.side_effect = refresh_user

    response = client.post(
        "/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["username"] == "john"
    assert response.json()["email"] == "john@example.com"
    assert response.json()["confirmed"] is False

    db.add.assert_called_once()
    db.commit.assert_called()
    db.refresh.assert_called_once()
    mock_send_email.assert_called_once_with(
        "john@example.com",
        "verification-token",
    )


def test_register_duplicate_email(client, db):
    db.scalar.return_value = User(
        username="existing",
        email="john@example.com",
        password="hashed",
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A user with this email already exists"
    )


@patch("app.routes.auth.send_verification_email")
@patch("app.routes.auth.create_verification_token")
def test_register_email_failure(
    mock_create_token,
    mock_send_email,
    client,
    db,
):
    db.scalar.return_value = None
    mock_create_token.return_value = "verification-token"
    mock_send_email.side_effect = Exception("SMTP error")

    response = client.post(
        "/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == ("Could not send verification email")
    db.delete.assert_called_once()
    assert db.commit.call_count == 2


@patch("app.routes.auth.verify_verification_token")
def test_verify_email_success(
    mock_verify_token,
    client,
    db,
):
    user = User(
        username="john",
        email="john@example.com",
        password="hashed",
        confirmed=False,
    )
    mock_verify_token.return_value = "john@example.com"
    db.scalar.return_value = user

    response = client.get(
        "/auth/verify-email",
        params={"token": "valid-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Email verified successfully",
    }
    assert user.confirmed is True
    db.commit.assert_called_once()


@patch("app.routes.auth.verify_verification_token")
def test_verify_email_invalid_token(
    mock_verify_token,
    client,
    db,
):
    mock_verify_token.return_value = None

    response = client.get(
        "/auth/verify-email",
        params={"token": "invalid-token"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired verification token"
    )


@patch("app.routes.auth.verify_verification_token")
def test_verify_email_user_not_found(
    mock_verify_token,
    client,
    db,
):
    mock_verify_token.return_value = "john@example.com"
    db.scalar.return_value = None

    response = client.get(
        "/auth/verify-email",
        params={"token": "valid-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@patch("app.routes.auth.verify_verification_token")
def test_verify_email_already_verified(
    mock_verify_token,
    client,
    db,
):
    user = User(
        username="john",
        email="john@example.com",
        password="hashed",
        confirmed=True,
    )
    mock_verify_token.return_value = "john@example.com"
    db.scalar.return_value = user

    response = client.get(
        "/auth/verify-email",
        params={"token": "valid-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Email is already verified",
    }


def test_login_success(client, db):
    user = User(
        id=1,
        username="john",
        email="john@example.com",
        password=hash_password("secret123"),
        confirmed=True,
    )
    db.scalar.return_value = user

    response = client.post(
        "/auth/login",
        data={
            "username": "john@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_invalid_credentials(client, db):
    db.scalar.return_value = None

    response = client.post(
        "/auth/login",
        data={
            "username": "john@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_unconfirmed_user(client, db):
    user = User(
        id=1,
        username="john",
        email="john@example.com",
        password=hash_password("secret123"),
        confirmed=False,
    )
    db.scalar.return_value = user

    response = client.post(
        "/auth/login",
        data={
            "username": "john@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Email is not verified"
