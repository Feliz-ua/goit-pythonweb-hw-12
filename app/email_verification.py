import os

from dotenv import load_dotenv
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import URLSafeTimedSerializer


load_dotenv()

secret_key = os.getenv("JWT_SECRET_KEY")

if not secret_key:
    raise RuntimeError("JWT_SECRET_KEY is not set")


serializer = URLSafeTimedSerializer(
    secret_key,
    salt="email-verification",
)


def create_verification_token(email: str) -> str:
    return serializer.dumps({"email": email})


def verify_verification_token(
    token: str,
    max_age: int = 86400,
) -> str | None:
    try:
        data = serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

    email = data.get("email")

    if not isinstance(email, str):
        return None

    return email