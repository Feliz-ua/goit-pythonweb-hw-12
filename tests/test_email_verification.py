from app.email_verification import (
    create_verification_token,
    verify_verification_token,
)


def test_create_and_verify_email_token():
    email = "test@example.com"

    token = create_verification_token(email)
    result = verify_verification_token(token)

    assert result == email


def test_invalid_email_token():
    assert verify_verification_token("invalid-token") is None
