"""Durable static repository checks; no input code execution or automatic AI charges."""

import argparse
import logging
from contextlib import ExitStack
from threading import Event

from smartregression.composition import (
    account_service,
    personal_project_service,
    product_explorer_service,
    product_repo_assistant_service,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    stop = Event()
    with ExitStack() as stack:
        auth, _ = account_service(stack, required=True)
        projects = personal_project_service(auth)
        explorer = product_explorer_service(auth)
        assistant = product_repo_assistant_service(auth, explorer, projects, None)
        while True:
            try:
                worked = assistant.process_once()
            except Exception:
                logging.error("Repository watcher unavailable; retrying after bounded delay.")
                worked = False
            if args.once:
                return
            stop.wait(1 if worked else 5)


if __name__ == "__main__":
    main()
