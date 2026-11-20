# Repository assistant UI delivery self-check

Scope: new assistant/watch/notification interface; shared auth, theme, navigation
and report regressions were also exercised. This is implementation self-review,
not independent design/accessibility approval. Direction: existing DESIGN.md,
developer workspace, neutral/teal, ENERGY 1 / RHYTHM 2 / MOTION 1.

Evidence: `frontend/tests/repository-assistant.spec.mjs`, existing theme/workspace
tests, build/lint and actual captures under `var/uiux-playwright/assistant-*`.
Fixture captures are explicitly DEMO; they are not live product metrics.
Final browser run: 60 passed in 38.7s, including all 12 assistant cases.

## Hard gate

- R-02 PASS: no em dash in newly authored assistant UI copy; source identifiers/user data retain their original text.
- R-03 PASS: Light/Dark layout checked at 1440, 1024, 768, 375 and 320px without document overflow.
- R-17 PASS: file/unread counts derive from API replies, not marketing statistics.
- R-18 PASS: no testimonials or invented people were added.
- R-23 PASS: the requested feature adds one real project tab; no logo/image/icon assets or fictitious permissions were added.
- R-24 PASS: navigation points to existing project/Explorer routes, with SHA/path query state.
- R-25 PASS: existing foreground/muted/warning tokens are reused; theme AA checks and new dark source/header assertions pass.
- R-26 PASS: overview prompts, question submission, preview/consent, thread selection/creation, watch settings/check and read actions have working handlers and browser cases.
- R-27 PASS: loading, empty, partial, quota/provider failure and saved-result states are rendered and exercised.
- R-28 PASS: no decorative FAQ was introduced.
- R-32 PASS: controls have labels/native semantics; focus, theme keyboard and navigation regression cases pass.
- R-33 PASS: interface changes are React/CSS source files; no injected styling or external runtime patch script.
- R-34 PASS: Light/Dark share tokens and pass screenshot/CSS checks; the inherited green header leak was corrected.
- R-35 PASS: build and actual browser tests exercise new controls; synthetic API/Google boundaries are distinguished from live recovery evidence.
- R-36 PASS: no unmeasured performance, security certification or guaranteed impact claims.
- R-37 PASS: direction is existing DESIGN.md; this is an extension of the shipped local workspace.
- R-38 PASS: mock summaries/accounts are labelled DEMO in fixtures; product renders returned data and actual model names.

## Purpose gate

- R-01 PASS: no new gradients/glows; neutral surfaces preserve code-reading focus.
- R-04 PASS: no generic AI/sparkle/robot icons added; labels identify actions.
- R-06 PASS: existing system font for prose; monospace only for code, paths and SHAs.
- R-07 PASS: no decorative grid/background pattern added.
- R-08 PASS: arrows describe base-to-target or dependency chains, not CTA decoration.
- R-09 PASS: status/attempt text represents actual returned state; no decorative AI badges.
- R-10 PASS: no glassmorphism added.
- R-12 PASS: no per-card elevation; borders separate conversation from monitoring.
- R-13 PASS: no glow effects added.
- R-14 PASS: broad reading/conversation column and narrower operational controls follow distinct tasks.
- R-19 PASS: shared control feedback respects reduced motion; no extra entrance/floating animations.
- R-22 PASS: no generic illustrations were added.

## Liveliness

- Dials PASS: ENERGY 1 / RHYTHM 2 / MOTION 1 match the existing developer tool.
- Focal point PASS: reading/conversation occupies the main column; watches support it.
- Hierarchy PASS: project title, assistant title, messages and evidence details have distinct levels.
- Spacing PASS: separators divide overview, history, messages and composer; mobile stacks monitoring beneath.
- Accent PASS: shared teal identifies selected navigation and primary submission; warnings use semantic status colors.
- Identity PASS: SHA/path citations, two-snapshot changes and dependency chains are specific to SmartRegression.

## Craftsmanship and consistency

- C-1 PASS: existing design tokens/components are reused for product tasks, not a new template.
- C-2 PASS: every visible new action has an implemented route/handler and bounded error behavior.
- C-3 PASS: each region supports reading, asking, selecting scope or reviewing changes.
- C-4 PASS: long identifiers wrap, source scrolls locally, both themes and mobile are verified.
- C-5 PASS: no fabricated customers, metrics, review or acceptance claims.
- R-05 PASS: this is a developer workspace, without landing-page hero/pricing/social-proof sections.
- R-11 PASS: shared control radius and panel radius remain distinct; controls are not uniformly pill-shaped.
- R-15 PASS: actions say what happens: preview evidence, save watch, check changes, mark read.
- R-16 PASS: no AI marketing buzzwords added.
- R-20 PASS: commit evidence and static-coverage warnings retain product identity.
- R-21 PASS: existing direct Light/Dark toggle remains and both modes are checked.
- R-29 PASS: neutral surfaces plus teal accent; warning color conveys unavailable/partial state.
- R-30 PASS: existing SmartRegression workspace is extended; no unrelated dashboard is copied.
- R-31 PASS: visual decisions serve evidence reading and separation of conversation/monitoring.

Limits: this does not claim exhaustive assistive-technology testing, independent
review or live external webhook acceptance. Google 3.8 overload is an observed
upstream state; a successful fallback is not relabelled as a 3.8 success.
