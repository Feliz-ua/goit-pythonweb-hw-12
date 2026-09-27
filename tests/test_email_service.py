import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.email_service import send_verification_email


def smtp_environment():
    return {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "2525",
        "SMTP_USER": "mailer@example.com",
        "SMTP_PASSWORD": "smtp-password",
        "MAIL_FROM": "noreply@example.com",
        "FRONTEND_VERIFY_URL": "http://frontend.example.com/verify",
    }


def test_send_verification_email_success():
    smtp = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp

    with (
        patch.dict(
            "os.environ",
            smtp_environment(),
            clear=True,
        ),
        patch(
            "app.email_service.smtplib.SMTP",
            return_value=smtp_context,
        ) as smtp_class,
    ):
        result = send_verification_email(
            "user@example.com",
            "verification-token",
        )

    assert result is None
    smtp_class.assert_called_once_with(
        "smtp.example.com",
        2525,
    )
    smtp_context.__enter__.assert_called_once_with()
    smtp_context.__exit__.assert_called_once()

    smtp.starttls.assert_called_once_with()
    smtp.login.assert_called_once_with(
        "mailer@example.com",
        "smtp-password",
    )
    smtp.send_message.assert_called_once()

    message = smtp.send_message.call_args.args[0]

    assert message["Subject"] == "Verify your email address"
    assert message["From"] == "noreply@example.com"
    assert message["To"] == "user@example.com"

    body = message.get_content()

    assert (
        "http://frontend.example.com/verify?token=verification-token"
    ) in body
    assert "The link is valid for 24 hours." in body


@pytest.mark.parametrize(
    "missing_variable",
    [
        "SMTP_HOST",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "MAIL_FROM",
    ],
)
def test_send_verification_email_missing_setting(
    missing_variable,
):
    environment = smtp_environment()
    environment[missing_variable] = ""

    with (
        patch.dict(
            "os.environ",
            environment,
            clear=True,
        ),
        pytest.raises(RuntimeError) as error,
    ):
        send_verification_email(
            "user@example.com",
            "verification-token",
        )

    assert error.value.args[0].startswith("Missing email settings:")
    assert missing_variable in str(error.value)


def test_send_verification_email_default_values():
    environment = smtp_environment()
    environment.pop("MAIL_FROM")
    environment.pop("FRONTEND_VERIFY_URL")

    smtp = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp

    with (
        patch.dict(
            "os.environ",
            environment,
            clear=True,
        ),
        patch(
            "app.email_service.smtplib.SMTP",
            return_value=smtp_context,
        ) as smtp_class,
    ):
        send_verification_email(
            "user@example.com",
            "verification-token",
        )

    smtp_class.assert_called_once_with(
        "smtp.example.com",
        2525,
    )

    message = smtp.send_message.call_args.args[0]

    assert message["From"] == "mailer@example.com"
    assert (
        "http://localhost:3000/verify-email?token=verification-token"
    ) in message.get_content()


def test_send_verification_email_smtp_error():
    environment = smtp_environment()

    with (
        patch.dict(
            "os.environ",
            environment,
            clear=True,
        ),
        patch(
            "app.email_service.smtplib.SMTP",
            side_effect=smtplib.SMTPException("SMTP unavailable"),
        ),
        pytest.raises(smtplib.SMTPException),
    ):
        send_verification_email(
            "user@example.com",
            "verification-token",
        )
