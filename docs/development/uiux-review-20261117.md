# UI/UX product analysis and local review

Reviewed against main `a55e44b` and the local UI branch in `D:\C1.SE26\Repo`.
Sources are the repository routes, contracts, current screens and the installed
[evondevKit UI/UX skill](../../.agents/skills/ui-ux/SKILL.md). Its nine examples are
alternative modes of work, not a nine-step process. This task used product/flow
analysis, a shared control contract, existing-UI review and dark-mode guidance.
The user explicitly delegated visual choices and fixes; a new wireframe approval
round was not required by the user's request. This is self-review with local
verification, not independent usability research or a claim of full WCAG compliance.

## Brief and navigation

- Product: repository change/impact analysis with personal project management
  (README, application routes and contracts).
- Users: developers, QA and the student team reviewing changes (project scope;
  no user interviews or usage percentages were invented).
- Main job: open a repo snapshot, select a file, inspect static impact/evidence,
  then optionally compare changes or read a saved analysis (code).
- Useful differentiation: tree, graph and evidence/impact coexist in the project
  workspace. Management settings are secondary to exploring code (design decision).
- Direction: labeled navigation, native system typography, flat neutral surfaces,
  restrained blue actions, shared light/dark layout. Large decorative charts and
  invented metrics would distract from this job (design decision).

| Screen | Primary job | Layout decision |
| --- | --- | --- |
| Authentication / account | Access and manage a personal account | Focused form; saved theme also applies here |
| `/app` | Resume a project or load a real reporting snapshot | Actual project links, filters and saved-report entry; no placeholder metrics |
| `/app/projects` | Find, create or archive personal projects | Search plus project cards and one create action |
| `/app/projects/:id` | Explore source and potential static impact | Compact header, project sections, tree / graph / inspector |
| Project what-if and run views | Compare a proposal or inspect a saved analysis | Keep hypothesis, static overlay, execution and AI status distinct |
| `/reports` | Open an exported JSON file independently of login | Real file picker/drop target and validated report; no invented server-side library |

For a returning signed-in user without a restored selection, `/app` → project →
file requires two user actions across two application screens after login. First
snapshot acquisition is bounded and static. Saved links read cache until explicitly
reopened. Importing a report stays on one application screen plus the OS file picker.
These are code-derived flow counts, not measured completion times.

## Shared control contract

| Primitive | Applied convention |
| --- | --- |
| Button | 40px, 10px radius, 500 weight; filled primary, outline secondary, text or icon action; 44px mobile report actions |
| State badge | Compact shape with text plus semantic color; success / partial / failed / not run remain distinct |
| Input | Visible label, theme-aware surface and focus ring; no decorative leading icon |
| Panel | 18–24px padding, 8–12px radius; adjacent work panels have explicit boundaries |
| List row | Entire real destination is actionable, with a visible hover/focus state |
| Dialog | Reuse ConfirmDialog, preserve Cancel, Escape and focus return |
| Empty/loading/error | Distinguish no records from unavailable data; give an existing next action |

Dark mode uses a charcoal page, brighter work surfaces and a brighter overlay layer.
Graph nodes, labels, controls, file source and report semantic states follow those
tokens; images are not inverted. A three-choice theme menu supports keyboard,
Escape and outside clicks. The default follows the OS. Normal browser storage
remembers choices; when storage is blocked, the current SPA session remains usable
and a full document reload falls back to the OS preference.

## Findings and resulting changes

| # | Finding / source | Classification | Result |
| --- | --- | --- | --- |
| 1 | Saved reports were an unstyled standalone form (original screenshot/code) | Inconsistent layout | Shared shell, file import panel, drop target and report toolbar |
| 2 | Dashboard before a reporting snapshot showed only filters and a notice (code) | Unclear next action | Actual project continuation links and report entry; no invented figures |
| 3 | Tall project heading delayed the code workspace (screenshots/code) | Layout preference | Removed redundant heading copy and reduced header spacing |
| 4 | Mixed anchor/button treatment and abrupt controls (user screenshot) | Inconsistent controls | Shared 10px control radius, lighter weight, restrained hover/press feedback; reduced motion respected |
| 5 | No appearance choice; fixed white surfaces (code) | Missing requested behavior | Light / dark / OS choice, pre-paint initialization, persistence and cross-tab updates |
| 6 | Login eyebrow text measured 3.12:1 on dark by the installed probe | Contrast failure | Theme-aware muted text; probe no longer reports this failure |
| 7 | Skip link retained a white surface on dark (probe/code; visible on keyboard focus) | Theme inconsistency | Theme-aware overlay surface and readable text |
| 8 | Explorer tree/canvas/inspector still had hardcoded white backgrounds (actual local screenshot) | Dark-mode failure | Shared surface/foreground tokens; regression assertions cover all three panels |
| 9 | Legacy 1200px rule moved the inspector below a three-column layout at 1152px (code) | Responsive inconsistency | Explicit default column and 1100px breakpoint; browser assertion added |
| 10 | Repeated alternate labels in user screenshots were absent from source | External translation suspected | Kept one source label; Vietnamese language and no-translation hints; extensions can override hints |

The original failing probe outputs remain under ignored `var/uiux-probe-login-dark/`
and `var/uiux-probe-reports-dark/`; final outputs are stored separately, not relabeled.

## Verification and limits

- 29 browser tests passed, covering project workspace, dashboard, JSON import,
  download bytes, invalid/oversized input, drag/drop, themes, keyboard, cross-tab
  preference sync, blocked storage, pre-React theme initialization, print and
  representative AA text contrast pairs in both palettes.
- Report dark layouts were checked at 375/768/1024/1280/1440/1920px. Existing light
  layouts have five-width coverage plus the 1152px inspector regression case.
- Installed-skill final dark probes: reports at six widths and login at
  375/1280/1920px, both with zero items classified “Hỏng”. Remaining advisories:
  expected signed-out 401; native file input hidden behind a real custom button;
  scrollbar parsing; differently sized format-description rows; password input
  width measured without its adjacent show/hide button. These do not disappear
  from the stored probe logs and do not constitute a full accessibility audit.
- Lint, TypeScript/Vite build and 179 existing contract/SSR checks passed during
  this implementation. Vite retains its large-chunk advisory. No backend,
  database schema, auth ownership or AI budget rules changed.
- Manual local verification used the synthetic QA account, real public TinyDB
  source/impact, a DEMO report import, theme switching and Cancel in the logout
  dialog. The user's hosted account and production deployment were not tested.

Final local screenshots are in `var/uiux-dashboard-light-final.jpg`,
`var/uiux-dashboard-dark-final.jpg`, `var/uiux-reports-dark-final.jpg` and
`var/uiux-workspace-dark-final.jpg`. Frontend/backend remain running for review.
No commit, push or deployment was performed.
