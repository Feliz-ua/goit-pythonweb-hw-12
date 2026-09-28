"""Authentication and password reset routes."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.email_service import (
    send_password_reset_email,
    send_verification_email,
)
from app.email_verification import (
    create_verification_token,
    verify_verification_token,
)
from app.models import User
from app.password_reset import (
    consume_reset_token,
    create_reset_token,
    delete_reset_token,
)
from app.schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a user and send an email verification link."""

    statement = select(User).where(User.email == body.email)
    existing_user = db.scalar(statement)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        username=body.username,
        email=body.email,
        password=hash_password(body.password),
        confirmed=False,
        role="user",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_verification_token(user.email)

    try:
        send_verification_email(user.email, token)
    except Exception as error:
        db.delete(user)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not send verification email",
        ) from error

    return user


@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    """Verify a user's email address using a signed token."""

    email = verify_verification_token(token)

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    statement = select(User).where(User.email == email)
    user = db.scalar(statement)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.confirmed:
        return {"message": "Email is already verified"}

    user.confirmed = True
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/password-reset")
def request_password_reset(
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Create a reset token and send a password reset link."""

    statement = select(User).where(User.email == body.email)
    user = db.scalar(statement)

    if user is not None:
        token = create_reset_token(user.id)

        try:
            send_password_reset_email(user.email, token)
        except Exception as error:
            delete_reset_token(token)

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send password reset email",
            ) from error

    return {
        "message": (
            "If the email exists, a password reset link has been sent."
        ),
    }


@router.post("/password-reset/confirm")
def confirm_password_reset(
    body: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Reset the password using a one-time Redis token."""

    user_id = consume_reset_token(body.token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user.password = hash_password(body.new_password)
    db.commit()

    return {
        "message": "Password has been reset successfully",
    }


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """Authenticate a confirmed user and return a JWT access token."""

    statement = select(User).where(User.email == form_data.username)
    user = db.scalar(statement)

    if user is None or not verify_password(
        form_data.password,
        user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email is not verified",
        )

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }