---
name: accessibility-review
description: Use when reviewing or changing frontend semantics, keyboard interaction, focus, contrast, responsive layout, forms, or accessible status messaging.
---

# Accessibility review

Review the user-visible path and report findings with page/component, trigger,
impact, and evidence. Fix only when the task authorizes changes.

- Check semantic landmarks and heading order, labels/names, control roles, and status
  messages that do not rely on color alone.
- Operate the path by keyboard; check visible focus, logical order, escape/return
  behavior where relevant, and no keyboard trap.
- Inspect zoom/reflow and narrow viewport behavior, text contrast, target usability,
  and error recovery. Do not claim WCAG conformance from a manual spot check.
- Use automated checks as a supplement; record tool/browser/version and limitations.
- For analysis states, ensure DEMO, pending, unknown, empty, failed discovery, fallback
  and execution outcome remain distinguishable and understandable.

External reference: github/awesome-copilot `agents/accessibility.agent.md` and
`skills/web-design-reviewer`, MIT repository, `main` (not commit-pinned). Adapted;
no external text/assets copied. See frontend profile and rule 03.
