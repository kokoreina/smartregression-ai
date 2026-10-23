# 1.08 - Run lifecycle

Proposed semantics exercised with immutable in-memory objects. Author: Nguyen Tan
Huy; proposed reviewer: Tran Hung Khanh. [Code](../../../backend/src/smartregression/application/sprint1_prototypes.py)
is not a job service, durable store, worker or public report schema.

| From | To | Timestamp and failure behavior |
| --- | --- | --- |
| create | queued | New UUID; created_at = updated_at; timezone required |
| queued | running | Set started_at and updated_at |
| queued | failed | Set finished_at; no started_at |
| running | completed | Set finished_at; no failure reason |
| running | failed | Set finished_at and allowlisted reason |
| terminal or same-state duplicate | reject | invalid_transition; old object unchanged |

Timestamps cannot move backwards. Failure codes: access_denied, invalid_revision,
dependency_unavailable, internal_error. Raw exception/source/credential text rejected.
A completed transition in a unit test is not proof of actual analysis completion.

## Retry and duplicates

Each create allocates a new UUID. Submission deduplication/idempotency unsupported.
Repeated same-state transitions rejected; terminal runs cannot reopen. Prototype
retry means a new run. retry_of linkage, fingerprint, retention and concurrency/CAS
are pending team decisions. Direct dataclass construction is not an untrusted-input
parser; only create/transition behavior is exercised. No durable history is stored.

Future flow: API authorizes request -> application resolves frozen repo/SHA identity
-> persist run -> isolated worker dispatch -> validate worker observations -> update
run. Never execute input repository code inside web API. run_id differs from report_id
and test_id. Existing analysis_status/execution_status are not job lifecycle states.
Cancellation/partial results and transport schema need separate contract review.

Pending: 1.04 access; An's 1.06 frozen SHA/PR semantics; Khanh's isolation/transport/
timeouts; An/Viet/Khanh consumer review; team durability and production retry policy.
No DB, migration, endpoint, worker or existing shared model changed.
