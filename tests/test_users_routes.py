from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models import User


@pytest.fixture
def current_user():
    return User(
        id=1,
        username="john",
        email="john@example.com",
        password="hashed-password",
        avatar=None,
        confirmed=True,
    )


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def client(current_user, db):
    app.dependency_overrides[get_current_user] = lambda: current_user

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_read_current_user(client, current_user):
    response = client.get("/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == current_user.id
    assert response.json()["username"] == current_user.username
    assert response.json()["email"] == current_user.email


def test_update_avatar_invalid_type(client):
    response = client.patch(
        "/users/avatar",
        files={
            "file": (
                "document.txt",
                b"not an image",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only JPEG, PNG and WEBP images are allowed"
    )


@patch("app.routes.users.cloudinary.uploader.upload")
def test_update_avatar_success(
    mock_upload,
    client,
    current_user,
):
    mock_upload.return_value = {
        "secure_url": "https://cdn.example.com/avatar.jpg",
    }

    response = client.patch(
        "/users/avatar",
        files={
            "file": (
                "avatar.jpg",
                b"fake image content",
                "image/jpeg",
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["avatar"] == ("https://cdn.example.com/avatar.jpg")

    mock_upload.assert_called_once_with(
        b"fake image content",
        folder="contacts/avatars",
        resource_type="image",
    )

    assert current_user.avatar == ("https://cdn.example.com/avatar.jpg")
