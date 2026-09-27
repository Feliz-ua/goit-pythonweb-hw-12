"""Redis client configuration and user-cache helpers."""

import json
import os
from typing import Any

import redis
from dotenv import load_dotenv


load_dotenv()


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)
USER_CACHE_TTL = int(
    os.getenv("REDIS_USER_TTL", "900"),
)


redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


def user_cache_key(user_id: int) -> str:
    """Return the Redis key used for a cached user."""
    return f"user:{user_id}"


def serialize_user(user: Any) -> str:
    """Serialize the user fields needed by the API response."""
    return json.dumps(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar,
            "confirmed": user.confirmed,
        }
    )


def cache_user(user: Any) -> None:
    """Store a user in Redis with a finite TTL."""
    redis_client.setex(
        user_cache_key(user.id),
        USER_CACHE_TTL,
        serialize_user(user),
    )


def get_cached_user(user_id: int) -> dict[str, Any] | None:
    """Return a cached user payload, or ``None`` on a cache miss."""
    cached_user = redis_client.get(user_cache_key(user_id))

    if cached_user is None:
        return None

    return json.loads(cached_user)


def delete_cached_user(user_id: int) -> None:
    """Remove a cached user from Redis."""
    redis_client.delete(user_cache_key(user_id))