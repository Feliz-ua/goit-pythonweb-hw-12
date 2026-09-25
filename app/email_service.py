import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


def send_verification_email(
    recipient: str,
    token: str,
) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    mail_from = os.getenv("MAIL_FROM", smtp_user)
    frontend_verify_url = os.getenv(
        "FRONTEND_VERIFY_URL",
        "http://localhost:3000/verify-email",
    )

    required_settings = {
        "SMTP_HOST": smtp_host,
        "SMTP_USER": smtp_user,
        "SMTP_PASSWORD": smtp_password,
        "MAIL_FROM": mail_from,
    }

    missing_settings = [
        name for name, value in required_settings.items() if not value
    ]

    if missing_settings:
        raise RuntimeError(
            "Missing email settings: " + ", ".join(missing_settings)
        )

    verification_url = f"{frontend_verify_url}?token={token}"

    message = EmailMessage()
    message["Subject"] = "Verify your email address"
    message["From"] = mail_from
    message["To"] = recipient
    message.set_content(
        "Please verify your email address by opening this link:\n\n"
        f"{verification_url}\n\n"
        "The link is valid for 24 hours."
    )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)