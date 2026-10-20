---
name: ui-design
description: Use when designing or materially changing SmartRegression dashboard, report, loading, empty, error, or evidence views.
---

# UI design for the dashboard

1. Inspect existing React/CSS patterns, generated contract, fixtures and the relevant
   Frontend/Dashboard profile before editing. Keep the change within the task scope.
2. Design for the actual user task: identify repository and commit range, understand
   impact evidence, inspect selection/fallback, and distinguish run status from test
   outcomes. Keep the next action clear.
3. Reuse current design language. Use hierarchy, spacing, readable tables and concise
   labels; support narrow screens and long paths/identifiers. Avoid adding a UI library
   or visual system without authorization.
4. Render unknown/null as unknown or not measured, empty inventory separately from
   discovery failure, and DEMO visibly. Do not fabricate analysis data or imply an
   unsupported backend state.
5. Include keyboard focus, semantic controls and accessible names. Verify with local
   checks and rendered browser inspection only where those tools actually exist.

External reference: github/awesome-copilot `skills/web-design-reviewer/SKILL.md`,
MIT repository, `main` (not commit-pinned). Adapted to this repo; no external file
or assets copied. Follow profile `docs/agents/frontend-dashboard.md` and rules 02/03/06.
