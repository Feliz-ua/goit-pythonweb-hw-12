import hashlib
import secrets

import redis

from app.redis_client import redis_client

RESET_TTL = 900


def _key(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"password-reset:{digest}"


def create_reset_token(user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    redis_client.setex(_key(token), RESET_TTL, str(user_id))
    return token


def consume_reset_token(token: str) -> int | None:
    key = _key(token)
    user_id = redis_client.get(key)

    if user_id is None:
        return None

    redis_client.delete(key)
    return int(user_id)

def delete_reset_token(token: str) -> None:
    """Delete a password reset token from Redis."""
    redis_client.delete(_key(token))