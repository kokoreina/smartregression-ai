"""Opt-in local auth/Gmail smoke. Never persist passwords, tokens or recipients.

Targets only the sender's own configured Gmail inbox. This is not a unit/CI test.
Email receipt and link confirmation require an actual user observation.
"""

import argparse
import json
import secrets
import smtplib
import ssl
import sys
from pathlib import Path

import httpx
from email_validator import validate_email

from smartregression.adapters.storage.auth_store import PostgresAuthStore
from smartregression.adapters.storage.config import load_database_settings
from smartregression.adapters.storage.connection import database_engine
from smartregression.auth_config import AuthSettings, web_environment

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action",
        choices=["register", "resend", "check", "request-reset", "smtp-check"],
        required=True,
    )
    args = parser.parse_args()
    env = web_environment()
    email = validate_email(
        env["SMARTREGRESSION_SMTP_USERNAME"], check_deliverability=False
    ).normalized.lower()
    if args.action == "smtp-check":
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                smtp.login(email, env["SMARTREGRESSION_SMTP_PASSWORD"].replace(" ", ""))
            print("SMTP TLS/login accepted; this does not prove inbox delivery.")
            return 0
        except smtplib.SMTPAuthenticationError:
            print("SMTP authentication_failed; check Gmail App Password, not account password.")
            return 1
        except OSError:
            print("SMTP connection_failed; network/port/TLS needs checking.")
            return 1
    if args.action == "check":
        settings = AuthSettings.load(env)
        with database_engine(
            load_database_settings(env, allow_loopback_test=settings.local_http)
        ) as engine:
            with PostgresAuthStore(engine).transaction() as tx:
                user = tx.user_by_email(email)
                assert user is not None
                result = {
                    "account_exists": True,
                    "verified": user.verified,
                    "enabled": user.enabled,
                    "email_receipt_observed": False,
                    "browser_acceptance": False,
                }
        (ROOT / "var/phase2/mail-account-state.json").write_text(json.dumps(result, indent=2))
        print("Server account state checked; verified=" + str(result["verified"]))
        return 0
    with httpx.Client(base_url="http://127.0.0.1:5173", trust_env=False, timeout=30) as client:

        def post(path, body):
            response = client.get("/api/v1/auth/csrf")
            response.raise_for_status()
            return client.post(
                "/api/v1/auth/" + path,
                json=body,
                headers={
                    "Origin": "http://127.0.0.1:5173",
                    "X-CSRF-Token": response.json()["token"],
                },
            )

        if args.action == "register":
            # Ephemeral credential only. Use recovery email later to choose your own password.
            password = secrets.token_urlsafe(24)
            response = post(
                "register",
                {"email": email, "password": password, "display_name": "Huy - Gmail acceptance"},
            )
        else:
            response = post(
                "resend-verification" if args.action == "resend" else "forgot-password",
                {"email": email},
            )
        assert response.status_code == 202
    print("Account request accepted; email delivery/receipt is not yet verified.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print("Account smoke failed; private values withheld.", file=sys.stderr)
        sys.exit(1)
