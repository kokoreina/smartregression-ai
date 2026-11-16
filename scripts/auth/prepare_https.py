"""Generate private loopback Compose configuration without touching existing DB.

CA and DB key are local project artifacts, never installed in the host trust store.
Gmail configuration is copied privately from the already authorized backend config.
"""

import ipaddress
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from sqlalchemy.engine import URL

from smartregression.auth_config import web_environment

ROOT = Path(__file__).resolve().parents[2]


def main():
    directory = ROOT / "var/local-https"
    if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
        raise ValueError("unsafe_workspace")
    if (directory / "runtime.env").exists():
        print("Local HTTPS configuration already exists; credentials preserved.")
        return
    directory.mkdir(parents=True, exist_ok=True)
    tls = directory / "tls"
    tls.mkdir(exist_ok=True)
    now = datetime.now(UTC)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "SmartRegression local DB test CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(True, False, False, False, False, True, True, False, False), critical=True
        )
        .sign(key, hashes.SHA256())
    )
    dbkey = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    dbcert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "db")]))
        .issuer_name(name)
        .public_key(dbkey.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=90))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName("db"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
            ),
            critical=False,
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(key, hashes.SHA256())
    )
    for path, value in [
        (tls / "ca.crt", ca.public_bytes(serialization.Encoding.PEM)),
        (tls / "db.crt", dbcert.public_bytes(serialization.Encoding.PEM)),
        (
            tls / "db.key",
            dbkey.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ),
        ),
    ]:
        path.write_bytes(value)
    # CA signing key is deliberately not persisted; rotate with an explicit setup.
    admin = secrets.token_urlsafe(40)
    runtime = secrets.token_urlsafe(40)

    def dsn(user, password):
        return URL.create(
            "postgresql+psycopg",
            username=user,
            password=password,
            host="db",
            database="smartregression_product",
            query={"sslmode": "verify-full", "sslrootcert": "/run/tls/ca.crt"},
        ).render_as_string(hide_password=False)

    env = web_environment()
    private = {
        "SMARTREGRESSION_WEB_MODE": "product",
        "SMARTREGRESSION_AUTH_LOCAL_HTTP": "0",
        "SMARTREGRESSION_FRONTEND_ORIGIN": "https://localhost:8443",
        "SMARTREGRESSION_CSRF_SECRET": secrets.token_urlsafe(48),
        "SMARTREGRESSION_DATABASE_URL": dsn("smartregression_product_runtime", runtime),
        "SMARTREGRESSION_SMTP_USERNAME": env.get("SMARTREGRESSION_SMTP_USERNAME", ""),
        "SMARTREGRESSION_SMTP_PASSWORD": env.get("SMARTREGRESSION_SMTP_PASSWORD", ""),
    }
    if any("\r" in v or "\n" in v for v in private.values()):
        raise ValueError("invalid_configuration")
    (directory / "runtime.env").write_text(
        "\n".join(k + "=" + v for k, v in private.items()) + "\n", encoding="utf-8"
    )
    (directory / "migration.env").write_text(
        "SMARTREGRESSION_MIGRATION_DATABASE_URL="
        + dsn("postgres", admin)
        + "\nSMARTREGRESSION_RUNTIME_DB_PASSWORD="
        + runtime
        + "\n",
        encoding="utf-8",
    )
    (directory / "postgres-password").write_text(admin, encoding="utf-8")
    print("Private local HTTPS configuration generated; host trust store unchanged.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("HTTPS preparation failed; private details withheld.") from None
