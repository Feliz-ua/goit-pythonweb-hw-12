"""FastAPI dependencies for database and authentication."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.redis_client import cache_user, get_cached_user
from app.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


DbSession = Annotated[Session, Depends(get_db)]
Token = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(
    token: Token,
    db: DbSession,
) -> User:
    """Validate JWT and return the current user from Redis or PostgreSQL."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (jwt.PyJWTError, ValueError, TypeError) as error:
        raise credentials_exception from error

    cached_user = get_cached_user(user_id)

    if cached_user is not None:
        return User(**cached_user)

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    cache_user(user)

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    """Allow access only to users with the admin role."""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


AdminUser = Annotated[User, Depends(require_admin)]