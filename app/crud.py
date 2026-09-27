"""Database CRUD operations for contacts."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Contact
from app.schemas import ContactCreate, ContactUpdate


def get_contacts(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Contact]:
    """Return contacts belonging to a specific user.

    Args:
        db: Active SQLAlchemy database session.
        user_id: Identifier of the contact owner.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of contacts owned by the specified user.
    """
    statement = (
        select(Contact)
        .where(Contact.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def get_contact(
    db: Session,
    contact_id: int,
    user_id: int,
) -> Contact | None:
    """Return one contact belonging to a specific user.

    Args:
        db: Active SQLAlchemy database session.
        contact_id: Identifier of the contact.
        user_id: Identifier of the contact owner.

    Returns:
        The requested contact, or ``None`` if it was not found.
    """
    statement = select(Contact).where(
        Contact.id == contact_id,
        Contact.user_id == user_id,
    )

    return db.scalar(statement)


def get_contact_by_email(
    db: Session,
    email: str,
    user_id: int,
) -> Contact | None:
    """Find a user's contact by email address.

    Args:
        db: Active SQLAlchemy database session.
        email: Email address to search for.
        user_id: Identifier of the contact owner.

    Returns:
        The matching contact, or ``None`` if no contact was found.
    """
    statement = select(Contact).where(
        Contact.email == email,
        Contact.user_id == user_id,
    )

    return db.scalar(statement)


def create_contact(
    db: Session,
    body: ContactCreate,
    user_id: int,
) -> Contact:
    """Create and persist a new contact.

    Args:
        db: Active SQLAlchemy database session.
        body: Validated contact creation data.
        user_id: Identifier of the contact owner.

    Returns:
        The newly created contact.
    """
    contact = Contact(
        **body.model_dump(),
        user_id=user_id,
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


def update_contact(
    db: Session,
    contact: Contact,
    body: ContactUpdate,
) -> Contact:
    """Update and persist an existing contact.

    Args:
        db: Active SQLAlchemy database session.
        contact: Contact instance to update.
        body: Validated replacement data.

    Returns:
        The updated contact.
    """
    for key, value in body.model_dump().items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)

    return contact


def remove_contact(
    db: Session,
    contact: Contact,
) -> None:
    """Delete a contact from the database.

    Args:
        db: Active SQLAlchemy database session.
        contact: Contact instance to delete.
    """
    db.delete(contact)
    db.commit()


def search_contacts(
    db: Session,
    query: str,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Contact]:
    """Search a user's contacts by common text fields.

    The search checks first name, last name, email address, and phone
    number.

    Args:
        db: Active SQLAlchemy database session.
        query: Text fragment used for searching.
        user_id: Identifier of the contact owner.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of matching contacts.
    """
    pattern = f"%{query}%"

    statement = (
        select(Contact)
        .where(
            Contact.user_id == user_id,
            or_(
                Contact.first_name.ilike(pattern),
                Contact.last_name.ilike(pattern),
                Contact.email.ilike(pattern),
                Contact.phone.ilike(pattern),
            ),
        )
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def get_upcoming_birthdays(
    db: Session,
    user_id: int,
    days: int = 7,
) -> list[Contact]:
    """Return contacts with birthdays in the upcoming period.

    The year of each birthday is replaced with the current year so
    that birthdays can be compared with today's date.

    Args:
        db: Active SQLAlchemy database session.
        user_id: Identifier of the contact owner.
        days: Number of days to search ahead.

    Returns:
        A list of contacts with upcoming birthdays.
    """
    today = datetime.now(UTC).date()
    end_date = today + timedelta(days=days)

    statement = select(Contact).where(Contact.user_id == user_id)
    contacts = db.scalars(statement).all()

    upcoming = []

    for contact in contacts:
        birthday = contact.birthday.replace(year=today.year)

        if birthday < today:
            birthday = birthday.replace(year=today.year + 1)

        if today <= birthday <= end_date:
            upcoming.append(contact)

    return upcoming