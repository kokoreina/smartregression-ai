---
name: github-actions-hardening
description: Use when creating, changing, or reviewing GitHub Actions workflows, triggers, permissions, expressions, third-party actions, or runner trust.
---

# GitHub Actions review

Read rule 12 and inspect the complete workflow plus called scripts/actions. Treat
PR titles, branch names, commit messages, artifacts and checked-out code as untrusted.

- Check trigger choice, fork behavior, `pull_request_target`/`workflow_run` boundaries,
  least-privilege `permissions`, secret availability and environment approvals.
- Trace `${{ }}` expressions into shell/script contexts; use safe environment passing
  and argument handling. Check `GITHUB_ENV`/`GITHUB_OUTPUT` writes and artifact trust.
- Check third-party action pinning and version provenance; preserve existing workflow
  behavior unless the task authorizes changes.
- Validate YAML/config locally where available; distinguish configured workflow from
  an observed successful GitHub run and from a required branch-protection check.
- Never alter repository settings, secrets or deployment permissions unless explicitly
  authorized. Do not run untrusted code with privileged credentials.

External reference: github/awesome-copilot `skills/github-actions-hardening`, MIT
repository, `main` (not commit-pinned). No upstream script/assets copied. Follow rules
05, 10, 12 and 14.
