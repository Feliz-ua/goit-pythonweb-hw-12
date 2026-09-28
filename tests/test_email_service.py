from unittest.mock import MagicMock, patch

import pytest

from app.email_service import (
    send_password_reset_email,
    send_verification_email,
)


@pytest.fixture
def smtp_settings(monkeypatch):
    settings = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "mailer@example.com",
        "SMTP_PASSWORD": "smtp-password",
        "MAIL_FROM": "noreply@example.com",
    }

    for name, value in settings.items():
        monkeypatch.setenv(name, value)

    return settings


def smtp_mock():
    smtp = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp
    smtp_context.__exit__.return_value = None
    return smtp, smtp_context


def test_send_verification_email(smtp_settings):
    smtp, smtp_context = smtp_mock()

    with patch(
        "app.email_service.smtplib.SMTP",
        return_value=smtp_context,
    ) as smtp_class:
        send_verification_email(
            "user@example.com",
            "verification-token",
        )

    smtp_class.assert_called_once_with(
        "smtp.example.com",
        587,
    )
    smtp.starttls.assert_called_once_with()
    smtp.login.assert_called_once_with(
        "mailer@example.com",
        "smtp-password",
    )
    smtp.send_message.assert_called_once()

    message = smtp.send_message.call_args.args[0]

    assert message["To"] == "user@example.com"
    assert message["From"] == "noreply@example.com"
    assert message["Subject"] == "Verify your email address"
    assert "verification-token" in message.get_content()


def test_send_password_reset_email(smtp_settings):
    smtp, smtp_context = smtp_mock()

    with patch(
        "app.email_service.smtplib.SMTP",
        return_value=smtp_context,
    ) as smtp_class:
        send_password_reset_email(
            "user@example.com",
            "reset-token",
        )

    smtp_class.assert_called_once_with(
        "smtp.example.com",
        587,
    )
    smtp.starttls.assert_called_once_with()
    smtp.login.assert_called_once_with(
        "mailer@example.com",
        "smtp-password",
    )
    smtp.send_message.assert_called_once()

    message = smtp.send_message.call_args.args[0]

    assert message["To"] == "user@example.com"
    assert message["From"] == "noreply@example.com"
    assert message["Subject"] == "Reset your password"
    assert "reset-token" in message.get_content()


def test_verification_email_uses_custom_frontend_url(
    smtp_settings,
    monkeypatch,
):
    monkeypatch.setenv(
        "FRONTEND_VERIFY_URL",
        "https://frontend.example.com/verify",
    )
    smtp, smtp_context = smtp_mock()

    with patch(
        "app.email_service.smtplib.SMTP",
        return_value=smtp_context,
    ):
        send_verification_email(
            "user@example.com",
            "token-123",
        )

    message = smtp.send_message.call_args.args[0]

    assert "https://frontend.example.com/verify?token=token-123" in (
        message.get_content()
    )


def test_password_reset_email_uses_custom_url(
    smtp_settings,
    monkeypatch,
):
    monkeypatch.setenv(
        "PASSWORD_RESET_URL",
        "https://frontend.example.com/reset",
    )
    smtp, smtp_context = smtp_mock()

    with patch(
        "app.email_service.smtplib.SMTP",
        return_value=smtp_context,
    ):
        send_password_reset_email(
            "user@example.com",
            "token-456",
        )

    message = smtp.send_message.call_args.args[0]

    assert "https://frontend.example.com/reset?token=token-456" in (
        message.get_content()
    )


@pytest.mark.parametrize(
    "function_name",
    [
        "send_verification_email",
        "send_password_reset_email",
    ],
)
def test_email_service_rejects_missing_settings(
    monkeypatch,
    function_name,
):
    for name in (
        "SMTP_HOST",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "MAIL_FROM",
    ):
        monkeypatch.delenv(name, raising=False)

    function = {
        "send_verification_email": send_verification_email,
        "send_password_reset_email": send_password_reset_email,
    }[function_name]

    with pytest.raises(RuntimeError, match="Missing email settings"):
        function(
            "user@example.com",
            "token",
        )


def test_smtp_error_is_propagated(smtp_settings):
    smtp, smtp_context = smtp_mock()
    smtp.send_message.side_effect = OSError("SMTP unavailable")

    with patch(
        "app.email_service.smtplib.SMTP",
        return_value=smtp_context,
    ):
        with pytest.raises(OSError, match="SMTP unavailable"):
            send_password_reset_email(
                "user@example.com",
                "token",
            )