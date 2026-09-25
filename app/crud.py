from datetime import date, timedelta

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
    for field, value in body.model_dump().items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    return contact


def remove_contact(db: Session, contact: Contact) -> None:
    db.delete(contact)
    db.commit()


def search_contacts(
    db: Session,
    query: str,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Contact]:
    pattern = f"%{query}%"

    statement = (
        select(Contact)
        .where(
            Contact.user_id == user_id,
            or_(
                Contact.first_name.ilike(pattern),
                Contact.last_name.ilike(pattern),
                Contact.email.ilike(pattern),
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
    today = date.today()
    end_date = today + timedelta(days=days)

    statement = select(Contact).where(Contact.user_id == user_id)
    contacts = db.scalars(statement).all()

    result = []

    for contact in contacts:
        birthday_this_year = contact.birthday.replace(year=today.year)

        if birthday_this_year < today:
            birthday_this_year = birthday_this_year.replace(
                year=today.year + 1,
            )

        if today <= birthday_this_year <= end_date:
            result.append(contact)

    return result
