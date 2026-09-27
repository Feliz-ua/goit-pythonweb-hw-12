from datetime import date, timedelta
from unittest.mock import MagicMock

from app import crud


def test_get_contacts():
    db = MagicMock()
    expected_contacts = [MagicMock(), MagicMock()]

    db.scalars.return_value.all.return_value = expected_contacts

    result = crud.get_contacts(db, user_id=1)

    assert result == expected_contacts
    db.scalars.assert_called_once()


def test_get_contact():
    db = MagicMock()
    expected_contact = MagicMock()

    db.scalar.return_value = expected_contact

    result = crud.get_contact(db, contact_id=1, user_id=2)

    assert result is expected_contact
    db.scalar.assert_called_once()


def test_get_contact_by_email():
    db = MagicMock()
    expected_contact = MagicMock()

    db.scalar.return_value = expected_contact

    result = crud.get_contact_by_email(
        db,
        email="test@example.com",
        user_id=2,
    )

    assert result is expected_contact
    db.scalar.assert_called_once()


def test_create_contact():
    db = MagicMock()

    body = MagicMock()
    body.model_dump.return_value = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+380501234567",
        "birthday": date(1990, 1, 1),
        "additional_data": None,
        "is_favorite": False,
    }

    result = crud.create_contact(db, body, user_id=1)

    assert result.user_id == 1
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    db.add.assert_called_once_with(result)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(result)


def test_update_contact():
    db = MagicMock()
    contact = MagicMock()

    body = MagicMock()
    body.model_dump.return_value = {
        "first_name": "Updated",
        "last_name": "User",
    }

    result = crud.update_contact(db, contact, body)

    assert result is contact
    assert contact.first_name == "Updated"
    assert contact.last_name == "User"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(contact)


def test_remove_contact():
    db = MagicMock()
    contact = MagicMock()

    result = crud.remove_contact(db, contact)

    assert result is None
    db.delete.assert_called_once_with(contact)
    db.commit.assert_called_once()


def test_search_contacts():
    db = MagicMock()
    expected_contacts = [MagicMock()]

    db.scalars.return_value.all.return_value = expected_contacts

    result = crud.search_contacts(
        db,
        query="john",
        user_id=1,
    )

    assert result == expected_contacts
    db.scalars.assert_called_once()


def test_get_upcoming_birthdays():
    db = MagicMock()
    today = date.today()

    contact = MagicMock()
    contact.birthday = today + timedelta(days=2)

    db.scalars.return_value.all.return_value = [contact]

    result = crud.get_upcoming_birthdays(
        db,
        user_id=1,
        days=7,
    )

    assert result == [contact]
