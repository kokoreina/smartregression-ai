---
name: webapp-testing
description: Use when a frontend change needs real-browser interaction, responsive verification, or debugging beyond static typecheck/lint.
---

# Browser verification

1. Confirm the app is already running or use an explicitly authorized local command;
   do not start background services without the environment's applicable permission.
2. Use an available browser automation tool. If none exists, report that rendered
   behavior remains unverified; do not add Playwright or other dependencies for a
   one-off check without scope authorization.
3. Exercise the changed user flow, including relevant loading, offline, empty/error,
   DEMO and keyboard states. Check console errors and a narrow/desktop viewport when
   the browser tool supports them.
4. Use repository fixtures or explicitly labeled mock data. Never infer production
   behavior from a DEMO fixture.
5. Report browser, URL, states exercised, observed result and gaps. A page HTTP 200 is
   not proof of visual correctness or end-to-end behavior.

External reference: github/awesome-copilot `skills/webapp-testing/SKILL.md`, MIT
repository, `main` (not commit-pinned). Adapted to existing tool availability; no
external scripts/assets copied. Follow rule 06.
