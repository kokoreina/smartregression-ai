# Sprint 3 feature acceptance — local scope

The canonical task state is the [75-task audit](sprint-3-phase-1-audit.md).
This matrix maps PB25–PB44 to consumers and observed evidence; it is not a second
backlog or independent approval. Baseline `5a30a7a`, branch
`feat/web-repository-analysis`, local uncommitted work, 15 November 2026.

Evidence is under ignored `var/phase3-8/` in this worktree. Synthetic GitHub
fixtures and SMTP test inboxes are labelled separately from saved live Gemini
reports. Browser checks use real PostgreSQL, a dedicated Chromium context and
actual SMTP delivery to the disposable inbox. They never extract email tokens
from database tables. Local HTTPS uses an explicit test certificate exception;
public TLS and staging email are not verified by this test.

| PB | Feature and consumer | Local evidence | Remaining boundary |
| --- | --- | --- | --- |
| PB25 | Accounts, session, consent and quota; auth/account views | Backend/auth PostgreSQL tests; `security-browser-https/result.json` covers reset/revocation, CSRF/Origin, 429 and multiple sessions | Gmail local was confirmed by Huy in phase 2; staging email pending |
| PB26 | Owner-scoped projects, CRUD/archive/restore | Project storage race/version tests; both HTTPS rehearsals | Three active projects; public GitHub only |
| PB27 | Snapshot tree, path search, select and TXT | HTTPS rehearsals: search Enter does not submit analysis; SHA/repository retained | 5,000 entries; acquisition limits remain |
| PB28 | Python/JS canonical graph, canvas/list/inspector | Independent graph fixtures; browser graph/source; Linux parser smoke in actual Compose backend | 150 canvas nodes; partial/unresolved labelled; no TS/JSX |
| PB29 | Immutable one-file code/diff and descriptive hypotheses | Scenario PostgreSQL/unit fixtures and browser payment.js overlays | No source execution, multi-file patches or repository writes |
| PB30 | Durable commit analysis, static-first and evidence | Run idempotency/recovery tests; browser run/reopen; live `sqlparse-run.json` | Static impact is potential impact; no regression tests executed |
| PB31 | Changed/direct/indirect file metrics | Independent chain/diamond/cycle/deletion fixtures and 40-file metric fixture | Unknown denominator is N/A; proportions are not fault probabilities |
| PB32 | History, persistent reports, pagination | PostgreSQL restart/restore campaign; browser canonical reload and history | Owner checks apply to read and download |
| PB33 | Personal/project dashboard and usage | Frozen repeatable-read summary/drilldown/CSV tests, mixed known/null/zero cost | Reservations are not billed cost; view expires after 24 hours |
| PB34 | Full JSON, backward-compatible offline import, CSV and print | Both rehearsals; `live-ai/offline-browser.json`; PDF visually inspected | 10,000 CSV rows; imported files are not authenticated server results |
| PB35 | Static reading guide and optional AI explanation | Config-based fixtures; one successful live reading guide | Unknown entrypoint stays unknown; explicit consent required |
| PB36 | Bounded lexical feature search and AI explanation | Vietnamese/accent/no-match fixtures; successful live search explanation | Lexical evidence does not establish semantic equivalence |
| PB37 | File/folder static context and optional explanation | Consent/excerpt/citation tests; live file explanation succeeded | **Folder live gate pending**: invalid output then provider configuration failure; campaign exhausted |
| PB38 | Static calls and bounded paths | Python/JS expected fixtures; browser clickable source/paths | Depth 10, 150 visited nodes, 20 paths; unresolved is explicit |
| PB39 | Compatible scenario A/B | Immutable replay/mismatch tests and browser A/B | Same repository/base/config/type; no automatic safety winner |
| PB40 | SCC, fan-in/out and module relationships | Independent graph fixtures and browser hotspots | Structural measures are not bugs or risk scores |
| PB41 | Versioned notes/pins and resume | PostgreSQL stale/version/retention tests; browser URL precedence and reopen | No AI draft autosave; stale anchors never move to another file |
| PB42 | Graph evolution between commits | Node/edge additions/removals fixtures and browser version view | Separate from what-if; deleted evidence uses base SHA |
| PB43 | Backend/contracts/security/storage/operations enabler | Full backend 1,103 passed / 172 skipped; PostgreSQL 167 passed / 4 historical skips; isolated restore; HTTPS security browser | Public staging, off-host backup, PR/main CI and independent review pending |
| PB44 | App shell/shared components/responsive/accessible UI enabler | Two 18-group HTTPS rehearsals; keyboard dialog/return-focus; 390/768/1440 widths; 200% text zoom; reduced-motion and 150-node profile | Self-check only; production browser coverage is not exhaustive |

The final [handoff](sprint-3-phase-3-8-handoff.md) records commands, artifacts,
restart/backup checks and known limitations. Technical self-verification must not
be represented as mentor/team acceptance or independent security review.

AI assistance: Codex supported implementation, tests and documentation. The author
still needs to review and understand the changes under the project's disclosure
policy; no signature, contribution percentage or academic approval is inferred.
