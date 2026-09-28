"""Redis helpers for user caching."""

import json
import os
from typing import Any

import redis
from dotenv import load_dotenv

from app.models import User


load_dotenv()


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0",
)
REDIS_USER_TTL = int(
    os.getenv("REDIS_USER_TTL", "900"),
)

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


def _user_key(user_id: int) -> str:
    return f"user:{user_id}"


def _user_to_dict(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password": user.password,
        "avatar": user.avatar,
        "confirmed": user.confirmed,
        "role": user.role,
    }


def cache_user(user: User) -> None:
    """Cache a user, including role, with a limited lifetime."""

    redis_client.setex(
        _user_key(user.id),
        REDIS_USER_TTL,
        json.dumps(_user_to_dict(user)),
    )


def get_cached_user(user_id: int) -> dict[str, Any] | None:
    """Return a cached user or None when the cache misses."""

    value = redis_client.get(_user_key(user_id))

    if value is None:
        return None

    return json.loads(value)


def delete_cached_user(user_id: int) -> None:
    """Delete a cached user."""

    redis_client.delete(_user_key(user_id))