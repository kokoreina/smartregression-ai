# Gemini adapter — task 3.04

`gemini.py` implements one generation attempt through `ProposalProvider`.
SDK async transport supports cancellation; the existing synchronous application
port uses its own event loop and rejects nested-loop use. Composition receives an
explicit backend credential; nothing calls Gemini on import or default analysis.

`pack_request` freezes authorized context, exact inventory IDs and evidence into
a bounded provider payload. Structured JSON is revalidated with canonical models,
then application checks provenance/membership. This is not semantic support,
selection, execution, source-egress authorization or budget admission.

Retry/deadline/session budgets, full-request count and opt-in synthetic live smoke
are implemented by [task 3.16](../../../../../docs/development/task-3.16.md).
Direct adapter use is for admitted calls/offline tests, not an
unguarded public endpoint. See [handoff](../../../../../docs/development/task-3.04.md).
