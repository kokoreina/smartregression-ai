# 1.04 - Repository access

Offline prototype by Nguyen Tan Huy; proposed reviewer: Do Ha An.
[Code](../../../backend/src/smartregression/application/sprint1_prototypes.py) and
[tests](../../../backend/tests/unit/test_sprint1_prototypes.py) use injected synthetic
status observations. No GitHub call, clone, credentials, API wiring or auth platform.

## Boundary

Input is owner/name with ASCII letters, numbers, underscores or hyphens, exactly
two segments. This deliberately limited subset excludes dotted repo names, URLs,
query strings, relative paths and shell commands. Validation is not authorization;
future caller must authorize and allowlist the canonical identity before transport.

| Observation | Outcome | Interpretation |
| --- | --- | --- |
| 200 | accessible | Observation only, no clone/write-rights proof |
| 401 | unauthorized | Credential cause not inferred |
| 403 | forbidden | Could be permission or rate policy |
| 404 | not_found_or_hidden | Missing and hidden private repo cannot be distinguished |
| 429/5xx/other | service_error | No automatic retry |
| TimeoutError/ConnectionError | service_error | Never echo exception text |
| Invalid identity | invalid_repository | Reject before transport |

Unexpected exceptions propagate for developer diagnosis, never expose their text
to UI. Future live adapter needs fixed GitHub host, bounded timeout/retry budget,
redirect policy, sanitized errors and backend-only credentials. No secrets in
identity, reports, logs or prompts. Repository text cannot grant tool permissions.

Tests exercise classification, invalid-input rejection before transport and timeout.
See [handoff](huy-handoff.md) for commands and limits. Real cases wait for Viet's
1.03 candidate/license, explicit network authorization and credentials supplied via
approved backend secret handling. An reviews revision/identity handoff. Shared
contracts unchanged; this internal spike is not a public API contract.
