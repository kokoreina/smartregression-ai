---
name: test-driven-development
description: Use when implementing a behavior change or bug fix that can be expressed as a focused automated regression test.
---

# Focused test-first workflow

1. Read rule 06 and the existing test/fixture conventions. State the expected behavior
   and smallest relevant boundary before editing.
2. Add or identify a test that fails for the reported defect, then run it and capture
   the actual failure. Do not write a test that merely restates the implementation.
3. Make the smallest change that satisfies the behavior; rerun the focused test, then
   the relevant broader checks from `docs/development/verified-commands.md`.
4. Keep environment/setup errors separate from code failures. Do not skip or weaken
   unrelated tests to claim success. Avoid new test dependencies unless authorized.
5. Report commands and results actually observed, including checks not run.

External reference: obra/superpowers `skills/test-driven-development/SKILL.md`, MIT
repo, `main` (not commit-pinned). This is an independently written adaptation;
no external scripts or text copied. This workflow does not override user instructions.
