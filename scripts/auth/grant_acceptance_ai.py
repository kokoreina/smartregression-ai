"""Apply the one explicit Sprint-3 USD .20 / ten-generation acceptance grant.

Only the verified configured sender account in the owned local DB can receive it.
Idempotent; never resets historical ledgers, balances, or existing requests.
"""

from migrate_local import main as upgrade_owned_database
from sqlalchemy import text
from sqlalchemy.engine import make_url

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine
from smartregression.auth_config import web_environment

CAMPAIGN = "sprint3-acceptance-20261115"


def main():
    upgrade_owned_database()
    env = web_environment()
    email = env["SMARTREGRESSION_SMTP_USERNAME"].strip().lower()
    settings = DatabaseSettings(
        make_url(env["SMARTREGRESSION_MIGRATION_DATABASE_URL"]), allow_loopback_test=True
    )
    with database_engine(settings) as engine, engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(741031)"))
        user = conn.execute(
            text(
                "SELECT id,verified,enabled FROM smartregression.web_users WH"
                "ERE email=:email FOR UPDATE"
            ),
            dict(email=email),
        ).first()
        if user is None or not user.verified or not user.enabled:
            raise ValueError("verified_configured_account_required")
        conn.execute(
            text(
                "INSERT INTO smartregression.web_ai_campaigns(id,max_calls,ca"
                "p_micro_usd) VALUES(:id,10,200000) ON CONFLICT(id) DO NOTHIN"
                "G"
            ),
            dict(id=CAMPAIGN),
        )
        campaign = conn.execute(
            text(
                "SELECT max_calls,cap_micro_usd FROM smartregression.web_ai_campaigns WHERE id=:id"
            ),
            dict(id=CAMPAIGN),
        ).one()
        if tuple(campaign) != (10, 200000):
            raise ValueError("existing_campaign_mismatch")
        existing = (
            conn.execute(
                text("SELECT owner_id FROM smartregression.web_ai_grants WHERE campaign_id=:id"),
                dict(id=CAMPAIGN),
            )
            .scalars()
            .all()
        )
        if any(identity != user.id for identity in existing):
            raise ValueError("existing_grant_owner_mismatch")
        conn.execute(
            text(
                "INSERT INTO smartregression.web_ai_grants(campaign_id,owner_"
                "id,max_calls,cap_micro_usd) VALUES(:id,:owner,10,200000) ON "
                "CONFLICT(campaign_id,owner_id) DO NOTHING"
            ),
            dict(id=CAMPAIGN, owner=user.id),
        )
    print("Acceptance grant configured: <=10 generations / USD 0.20; historical ledgers unchanged.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Acceptance grant failed; private details withheld.") from None
