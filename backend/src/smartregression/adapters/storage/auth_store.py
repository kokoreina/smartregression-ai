"""Bound SQL account storage. All account mutations serialize on the user row."""

from contextlib import contextmanager

from sqlalchemy import text

from smartregression.adapters.storage.connection import database_transaction
from smartregression.application.auth import User


class PostgresAuthStore:
    def __init__(self, engine):
        self.engine = engine

    @contextmanager
    def transaction(self):
        with database_transaction(self.engine) as connection:
            yield BoundAuthStore(connection)


class BoundAuthStore:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, statement, **parameters):
        return self.connection.execute(text(statement), parameters)

    @staticmethod
    def _user(row):
        return (
            User(
                str(row.id),
                row.email,
                row.display_name,
                row.password_hash,
                row.verified,
                row.enabled,
            )
            if row
            else None
        )

    def user_by_email(self, email):
        return self._user(
            self.execute(
                "SELECT * FROM smartregression.web_users WHERE email=:email", email=email
            ).first()
        )

    def user_by_id(self, user_id):
        return self._user(
            self.execute(
                "SELECT * FROM smartregression.web_users WHERE id=:id FOR UPDATE", id=user_id
            ).first()
        )

    def insert_user(self, user):
        return (
            self.execute(
                "INSERT INTO smartregression.web_users (id,email,display_name,password_hash) "
                "VALUES (:id,:email,:name,:password) ON CONFLICT(email) DO NOTHING RETURNING id",
                id=user.id,
                email=user.email,
                name=user.display_name,
                password=user.password_hash,
            ).first()
            is not None
        )

    def session_user(self, digest, now):
        user_id = self.execute(
            "SELECT user_id FROM smartregression.web_sessions WHERE digest=:digest", digest=digest
        ).scalar()
        if user_id is None:
            return None
        user = self.user_by_id(str(user_id))
        valid = self.execute(
            "SELECT 1 FROM smartregression.web_sessions "
            "WHERE digest=:digest AND expires_at>:now AND revoked_at IS NULL",
            digest=digest,
            now=now,
        ).scalar()
        return user if valid else None

    def create_session(self, digest, user_id, expires):
        self.execute(
            "INSERT INTO smartregression.web_sessions(digest,user_id,expires_at) "
            "VALUES (:digest,:user_id,:expires)",
            digest=digest,
            user_id=user_id,
            expires=expires,
        )

    def revoke_session(self, digest):
        # Always take the user lock first, including logout/rotation.
        user_id = self.execute(
            "SELECT user_id FROM smartregression.web_sessions WHERE digest=:digest", digest=digest
        ).scalar()
        if user_id:
            self.user_by_id(str(user_id))
            self.execute(
                "UPDATE smartregression.web_sessions SET revoked_at=CURRENT_TIMESTAMP "
                "WHERE digest=:digest AND revoked_at IS NULL",
                digest=digest,
            )

    def revoke_all(self, user_id):
        self.execute(
            "UPDATE smartregression.web_sessions SET revoked_at=CURRENT_TIMESTAMP "
            "WHERE user_id=:id AND revoked_at IS NULL",
            id=user_id,
        )
        self.execute(
            "UPDATE smartregression.web_account_tokens SET used_at=CURRENT_TIMESTAMP "
            "WHERE user_id=:id AND used_at IS NULL",
            id=user_id,
        )

    def create_token(self, digest, user_id, purpose, expires):
        self.execute(
            "UPDATE smartregression.web_account_tokens SET used_at=CURRENT_TIMESTAMP "
            "WHERE user_id=:id AND purpose=:purpose AND used_at IS NULL",
            id=user_id,
            purpose=purpose,
        )
        self.execute(
            "INSERT INTO smartregression.web_account_tokens(digest,user_id,purpose,expires_at) "
            "VALUES (:digest,:id,:purpose,:expires)",
            digest=digest,
            id=user_id,
            purpose=purpose,
            expires=expires,
        )

    def token_user(self, digest, purpose, now):
        value = self.execute(
            "SELECT user_id FROM smartregression.web_account_tokens "
            "WHERE digest=:digest AND purpose=:purpose AND expires_at>:now AND used_at IS NULL",
            digest=digest,
            purpose=purpose,
            now=now,
        ).scalar()
        return str(value) if value else None

    def consume_token(self, digest, purpose, now):
        return (
            self.execute(
                "UPDATE smartregression.web_account_tokens SET used_at=:now "
                "WHERE digest=:digest AND purpose=:purpose AND expires_at>:now AND used_at IS NULL "
                "RETURNING user_id",
                digest=digest,
                purpose=purpose,
                now=now,
            ).first()
            is not None
        )

    def set_verified(self, user_id):
        self.execute("UPDATE smartregression.web_users SET verified=TRUE WHERE id=:id", id=user_id)

    def set_password(self, user_id, password_hash):
        self.execute(
            "UPDATE smartregression.web_users SET password_hash=:password WHERE id=:id",
            password=password_hash,
            id=user_id,
        )

    def set_name(self, user_id, name):
        self.execute(
            "UPDATE smartregression.web_users SET display_name=:name WHERE id=:id",
            name=name,
            id=user_id,
        )

    def disable(self, user_id):
        self.execute("UPDATE smartregression.web_users SET enabled=FALSE WHERE id=:id", id=user_id)

    def take_limit(self, key, start, limit):
        # Conditional UPSERT is atomic even across separate application workers.
        return (
            self.execute(
                "INSERT INTO smartregression.web_rate_limits(key_hash,window_start,attempts) "
                "VALUES (:key,:start,1) ON CONFLICT (key_hash,window_start) DO UPDATE "
                "SET attempts=web_rate_limits.attempts+1 WHERE web_rate_limits.attempts<:limit "
                "RETURNING attempts",
                key=key,
                start=start,
                limit=limit,
            ).first()
            is not None
        )
