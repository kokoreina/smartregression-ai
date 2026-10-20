---
name: api-contracts
description: Use when changing Pydantic models, API/CLI report shape, OpenAPI, generated TypeScript, or any producer-consumer contract.
---

# Contract change workflow

1. Read rule 03, contract documentation and every affected producer/consumer. Backend
   models are the source of truth; generated OpenAPI and frontend types are outputs.
2. Check compatibility for required/optional/null/default, unknown fields, version,
   IDs, evidence provenance, and DEMO fixtures. Identify breaking changes and pending
   policy before changing the schema.
3. Update source models, then regenerate artifacts using documented commands. Never
   hand-edit generated files. Validate fixture with backend and check generated drift.
4. Keep API/CLI logic in application boundaries; do not create endpoints merely because
   a schema exists. Preserve stable errors and do not echo sensitive input.
5. Report impacted consumers, migration/version implications, actual checks and
   unsupported runtime behavior.

Project authority: `docs/rules/03-contracts-api.md` and `docs/contracts/README.md`.
External workflow reference: github/awesome-copilot `skills/docs-sync-audit` and
`skills/github-copilot-starter`, MIT repo, `main` (not commit-pinned); no source copied.
