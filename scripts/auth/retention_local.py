"""Operator-only dry-run by default, on the exact labelled local database."""

import argparse
import json

from owned_database import owned_database

from smartregression.adapters.storage.config import DatabaseSettings
from smartregression.adapters.storage.connection import database_engine
from smartregression.adapters.storage.retention import prune_cache


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    url, _ = owned_database()
    with database_engine(DatabaseSettings(url, allow_loopback_test=True)) as engine:
        print(json.dumps(prune_cache(engine, apply=args.apply)))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Owned cache retention failed; private details withheld.") from None
