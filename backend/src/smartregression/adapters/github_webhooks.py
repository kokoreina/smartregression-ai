"""Validate signed GitHub deliveries before extracting a bounded event projection."""

import hashlib
import hmac
import json
import re
from uuid import UUID

from smartregression.application.auth import AuthFailure
from smartregression.contracts.repo_assistant import WatchInput, WebhookReceipt


def receive_delivery(store, raw: bytes, headers, secret: str) -> WebhookReceipt:
    if len(secret.encode()) < 32:
        raise AuthFailure("github_webhook_unavailable", 503)
    expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    received = headers.get("x-hub-signature-256", "")
    if not re.fullmatch("sha256=[0-9a-f]{64}", received) or not hmac.compare_digest(
        expected, received
    ):
        raise AuthFailure("invalid_webhook_signature", 401)
    if len(raw) > 65536:
        raise AuthFailure("request_limit", 413)
    try:
        identity = str(UUID(headers.get("x-github-delivery", "")))
        event = headers.get("x-github-event", "")
        value = json.loads(raw)
        repository = value["repository"]["full_name"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", repository):
            raise ValueError()
        actor = value.get("sender", {}).get("login")
        if actor is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", actor):
            raise ValueError()
        if event == "push":
            ref = value["ref"]
            if not ref.startswith("refs/heads/"):
                return WebhookReceipt(accepted=False, duplicate=False, scheduled=0)
            branch = ref.removeprefix("refs/heads/")
            for key in ("before", "after"):
                if not re.fullmatch("[0-9a-f]{40}", value[key]):
                    raise ValueError()
        elif event in {"create", "delete"}:
            if value.get("ref_type") != "branch":
                return WebhookReceipt(accepted=False, duplicate=False, scheduled=0)
            branch = value["ref"]
        elif (
            event == "pull_request"
            and value.get("action") == "closed"
            and value["pull_request"].get("merged") is True
        ):
            # Fork PRs belong to their base repository; reconcile the authorized base ref.
            branch = value["pull_request"]["base"]["ref"]
            if value["pull_request"]["base"]["repo"]["full_name"].lower() != repository.lower():
                raise ValueError()
        elif event == "ping":
            return WebhookReceipt(accepted=True, duplicate=False, scheduled=0)
        else:
            return WebhookReceipt(accepted=False, duplicate=False, scheduled=0)
        WatchInput(branch=branch)
    except ValueError, KeyError, TypeError, AttributeError:
        raise AuthFailure("invalid_webhook_payload", 422) from None
    duplicate, count = store.delivery(
        identity, hashlib.sha256(raw).hexdigest(), repository, event, branch, actor
    )
    return WebhookReceipt(accepted=True, duplicate=duplicate, scheduled=count)
