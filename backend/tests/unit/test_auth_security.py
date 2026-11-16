"""Auth contracts and transport guards, independent of PostgreSQL and SMTP."""

import pytest
from pydantic import ValidationError

from smartregression.adapters.auth_security import CsrfSigner, PasswordHasher
from smartregression.contracts.auth import Registration


def test_registration_normalizes_email_without_trimming_password():
    value = Registration(
        email=" Huy@Example.com ", password=" a long password ", display_name=" Huy "
    )
    assert str(value.email) == "huy@example.com"
    assert value.password.get_secret_value() == " a long password "
    assert value.display_name == "Huy"
    assert "a long password" not in repr(value)


@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_password_length_is_enforced(password):
    with pytest.raises(ValidationError):
        Registration(email="huy@example.com", password=password, display_name="Huy")


def test_password_hash_is_salted_and_bad_hash_does_not_escape():
    hasher = PasswordHasher()
    first = hasher.hash("long enough password")
    assert first.startswith("$argon2id$")
    assert first != hasher.hash("long enough password")
    assert hasher.verify("long enough password", first)
    assert not hasher.verify("wrong password", first)
    assert not hasher.verify("wrong password", "corrupt")


def test_csrf_is_signed_expiring_and_bound_to_session():
    signer = CsrfSigner(b"x" * 32)
    token = signer.issue("session-a", now=100)
    assert signer.valid(token, token, "session-a", now=101)
    assert not signer.valid(token, token, "session-b", now=101)
    assert not signer.valid(token, token, "session-a", now=3701)
    assert not signer.valid(token, token, "session-a", now=99)
    assert not signer.valid(token, token + "x", "session-a", now=101)
    assert not signer.valid(token + "x", token + "x", "session-a", now=101)
    assert not signer.valid("é", "é", "session-a", now=101)
