from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas import ContactCreate, ContactResponse, ContactUpdate

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[ContactResponse])
def read_contacts(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):
    return crud.get_contacts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get("/search", response_model=list[ContactResponse])
def search(
    db: DbSession,
    current_user: CurrentUser,
    query: str = Query(min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
):
    return crud.search_contacts(
        db=db,
        query=query,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get("/birthdays", response_model=list[ContactResponse])
def upcoming_birthdays(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(default=7, ge=1, le=365),
):
    return crud.get_upcoming_birthdays(
        db=db,
        user_id=current_user.id,
        days=days,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
def read_contact(
    contact_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    contact = crud.get_contact(
        db=db,
        contact_id=contact_id,
        user_id=current_user.id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    body: ContactCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    existing_contact = crud.get_contact_by_email(
        db=db,
        email=body.email,
        user_id=current_user.id,
    )

    if existing_contact is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this email already exists",
        )

    return crud.create_contact(
        db=db,
        body=body,
        user_id=current_user.id,
    )


@router.put("/{contact_id}", response_model=ContactResponse)
def update(
    contact_id: int,
    body: ContactUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    contact = crud.get_contact(
        db=db,
        contact_id=contact_id,
        user_id=current_user.id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    existing_contact = crud.get_contact_by_email(
        db=db,
        email=body.email,
        user_id=current_user.id,
    )

    if (
        existing_contact is not None
        and existing_contact.id != contact_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this email already exists",
        )

    return crud.update_contact(
        db=db,
        contact=contact,
        body=body,
    )


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    contact_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    contact = crud.get_contact(
        db=db,
        contact_id=contact_id,
        user_id=current_user.id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    crud.remove_contact(db, contact)
