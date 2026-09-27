from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user
from app.main import app
from app.models import Contact, User
from app.routes.contacts import DbSession


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

    def override_db():
        yield db

    app.dependency_overrides[DbSession] = override_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def contact(contact_id=1, user_id=1):
    return Contact(
        id=contact_id,
        user_id=user_id,
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+380501234567",
        birthday=date(1990, 1, 1),
        additional_data=None,
        is_favorite=False,
    )


def test_read_contacts(client):
    contacts = [contact(), contact(contact_id=2)]

    with patch(
        "app.routes.contacts.crud.get_contacts",
        return_value=contacts,
    ) as mock_get:
        response = client.get("/contacts/")

    assert response.status_code == 200
    assert len(response.json()) == 2
    mock_get.assert_called_once_with(
        db=response and mock_get.call_args.kwargs["db"],
        user_id=1,
        skip=0,
        limit=100,
    )


def test_read_contacts_with_pagination(client):
    with patch(
        "app.routes.contacts.crud.get_contacts",
        return_value=[],
    ) as mock_get:
        response = client.get(
            "/contacts/",
            params={"skip": 10, "limit": 20},
        )

    assert response.status_code == 200
    assert response.json() == []
    assert mock_get.call_args.kwargs["skip"] == 10
    assert mock_get.call_args.kwargs["limit"] == 20


def test_search_contacts(client):
    with patch(
        "app.routes.contacts.crud.search_contacts",
        return_value=[contact()],
    ) as mock_search:
        response = client.get(
            "/contacts/search",
            params={"query": "john"},
        )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert mock_search.call_args.kwargs["query"] == "john"
    assert mock_search.call_args.kwargs["user_id"] == 1


def test_upcoming_birthdays(client):
    with patch(
        "app.routes.contacts.crud.get_upcoming_birthdays",
        return_value=[contact()],
    ) as mock_birthdays:
        response = client.get(
            "/contacts/birthdays",
            params={"days": 14},
        )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert mock_birthdays.call_args.kwargs["days"] == 14
    assert mock_birthdays.call_args.kwargs["user_id"] == 1


def test_read_contact_success(client):
    with patch(
        "app.routes.contacts.crud.get_contact",
        return_value=contact(),
    ):
        response = client.get("/contacts/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["email"] == "john@example.com"


def test_read_contact_not_found(client):
    with patch(
        "app.routes.contacts.crud.get_contact",
        return_value=None,
    ):
        response = client.get("/contacts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"


@patch("app.routes.contacts.crud.create_contact")
@patch("app.routes.contacts.crud.get_contact_by_email")
def test_create_contact_success(
    mock_get_by_email,
    mock_create,
    client,
):
    mock_get_by_email.return_value = None
    new_contact = contact()
    mock_create.return_value = new_contact

    response = client.post(
        "/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+380501234567",
            "birthday": "1990-01-01",
            "additional_data": None,
            "is_favorite": False,
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "john@example.com"
    mock_create.assert_called_once()


@patch("app.routes.contacts.crud.get_contact_by_email")
def test_create_contact_duplicate_email(
    mock_get_by_email,
    client,
):
    mock_get_by_email.return_value = contact()

    response = client.post(
        "/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+380501234567",
            "birthday": "1990-01-01",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A contact with this email already exists"
    )


@patch("app.routes.contacts.crud.update_contact")
@patch("app.routes.contacts.crud.get_contact_by_email")
@patch("app.routes.contacts.crud.get_contact")
def test_update_contact_success(
    mock_get,
    mock_get_by_email,
    mock_update,
    client,
):
    existing = contact()
    mock_get.return_value = existing
    mock_get_by_email.return_value = None
    mock_update.return_value = existing

    response = client.put(
        "/contacts/1",
        json={
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "phone": "+380501234567",
            "birthday": "1990-01-01",
        },
    )

    assert response.status_code == 200
    mock_update.assert_called_once()


def test_update_contact_not_found(client):
    with patch(
        "app.routes.contacts.crud.get_contact",
        return_value=None,
    ):
        response = client.put(
            "/contacts/999",
            json={
                "first_name": "Updated",
                "last_name": "User",
                "email": "updated@example.com",
                "phone": "+380501234567",
                "birthday": "1990-01-01",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"


@patch("app.routes.contacts.crud.get_contact_by_email")
@patch("app.routes.contacts.crud.get_contact")
def test_update_contact_duplicate_email(
    mock_get,
    mock_get_by_email,
    client,
):
    mock_get.return_value = contact(contact_id=1)
    mock_get_by_email.return_value = contact(contact_id=2)

    response = client.put(
        "/contacts/1",
        json={
            "first_name": "Updated",
            "last_name": "User",
            "email": "john@example.com",
            "phone": "+380501234567",
            "birthday": "1990-01-01",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A contact with this email already exists"
    )


@patch("app.routes.contacts.crud.remove_contact")
@patch("app.routes.contacts.crud.get_contact")
def test_delete_contact_success(
    mock_get,
    mock_remove,
    client,
):
    contact_object = contact()
    mock_get.return_value = contact_object

    response = client.delete("/contacts/1")

    assert response.status_code == 204
    assert response.content == b""
    mock_remove.assert_called_once_with(
        mock_get.call_args.kwargs["db"],
        contact_object,
    )


def test_delete_contact_not_found(client):
    with patch(
        "app.routes.contacts.crud.get_contact",
        return_value=None,
    ):
        response = client.delete("/contacts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"
