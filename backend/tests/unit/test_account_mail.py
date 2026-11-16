"""No real email is sent by unit tests."""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from smartregression.adapters.account_mail import GmailMailer
from smartregression.application.auth import MailDeliveryError
from smartregression.auth_config import AuthSettings


def test_mail_uses_tls_fixed_origin_fragment_and_no_raw_diagnostics():
    client = MagicMock()
    client.send_message.return_value = {}
    with patch("smtplib.SMTP") as smtp:
        smtp.return_value.__enter__.return_value = client
        GmailMailer("group@example.com", "synthetic-password", "https://app.example.com").send(
            "huy@example.com", "verify", "synthetic-token"
        )
        smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
    client.starttls.assert_called_once()
    message = client.send_message.call_args.args[0]
    assert "https://app.example.com/verify-email#token=synthetic-token" in message.get_content()
    assert "synthetic-token" not in str(message["Subject"])
    assert "synthetic-password" not in repr(GmailMailer("a", "synthetic-password"))


def test_smtp_error_is_sanitized():
    with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("private server detail")):
        with pytest.raises(MailDeliveryError) as error:
            GmailMailer("group@example.com", "synthetic-password").send(
                "huy@example.com", "reset", "token"
            )
        assert "private" not in str(error.value)


@pytest.mark.parametrize(
    "origin,local",
    [
        ("http://public.example.com", True),
        ("http://app.example.com", False),
        ("https://app.example.com/", False),
        ("https://user:pass@app.example.com", False),
        ("https://app.example.com:999999", False),
    ],
)
def test_invalid_origin_settings_rejected(origin, local):
    with pytest.raises(ValueError, match="web_configuration_required"):
        AuthSettings(origin, b"x" * 32, local)
