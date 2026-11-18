# Nova-inspired local UI follow-up

## Scope and source preservation

Work remains in `D:\C1.SE26\Repo` on `feat/web-uiux-project-workspace`, based on the
existing local working tree, not a fresh GitHub checkout. No reset, checkout,
commit, push, backend/schema/generated-file change or new dependency was used.

The supplied `D:\Test Linh Tinh\smartregression_ui_kit.zip` was read locally:
`smartregression_codex_prompt.txt`, its README, HTML concept structure and all
seven images in UI_REFERENCE. The HTML's sample metrics/activity were not imported
into production UI. Reference assets remain in ignored `var/`; they were not
uploaded or copied into the application's public assets.

Before editing, 134 modified/untracked local files were preserved in
`var/nova-review-e0ccfa3c39/local-edits-before.zip`, with per-file SHA-256 hashes in
`local-edits-before.json`. The main implementation builds on those edits.

## Audit and chosen direction

Audit: React 19, Vite 7, TypeScript, plain CSS; existing @xyflow/react + Dagre,
ConfirmDialog, report views and repository tree were reused. Guidance applied:
the installed `ui-ux`, `ui-design`, `accessibility-review`, `webapp-testing` and
Frontend/Dashboard rules 02/03/06. The user delegated visual choices and fixes.

| Priority | Observation | Result |
| --- | --- | --- |
| High | Dark colors were split across token files and legacy selectors; the kit's old screenshot showed white work panels | A canonical token file defines both palettes; existing dark surface regression coverage is retained |
| High | Three panels leave little width for graph labels | Collapsible panels and expanded graph mode; mobile tabs retained |
| High | Small graph nodes and repeated edge labels obscure source navigation | Two/three-line nodes with actual kind/path, correct LR ports, optional folders/symbols/edge labels and selected-file camera |
| Medium | Headers, filters and card borders lack a single hierarchy | Inset workspace, compact filters and shared type/radius/spacing/motion tokens |
| Medium | Theme menu requires multiple actions | One click toggles light/dark, with keyboard and persistence coverage |

Two Explorer options were considered: (A) flexible three-pane workspace plus a
wide graph mode; (B) permanent two-pane workspace with a detail drawer. A was
chosen to preserve simultaneous tree/impact work on desktop and existing mobile
navigation. B was not implemented.

The Nova references inform spacing, typography and surface hierarchy. The result
uses a low-chroma teal accent on neutral surfaces. It keeps source/evidence as the
main content; there are no sales, revenue or artificial activity widgets.

## Source changes

- `frontend/src/app/design-tokens.css`: canonical light/dark semantic colors,
  control/panel/workspace radii, 4/8-based spacing, type and motion tokens.
- `workspace.css`, `themes.css`, `main.tsx`: inset shell, sidebar/header, compact
  overview filters, data cards/tables and report/form/graph theme integration.
- `ThemeToggle.tsx`, `theme.ts`, `public/theme-init.js`: direct toggle and matching
  browser theme color. Existing OS default, manual persistence, cross-tab sync,
  blocked-storage handling and pre-React initialization are retained.
- `Explorer.tsx`: display-only graph filtering, clearer node content and ports,
  preserved selection, zoom/Fit View, selected-file framing and collapsible panes.
  Expanding does not create new analysis or AI requests. The same source, notes,
  impact, evidence, reading guide and call-path controls remain available.
- Frontend browser tests: direct-toggle requirements, palette assertions,
  panel/camera/zoom interactions and responsive transitions were updated/extended.

The camera/layout changes do not alter impact algorithms, snapshots, API request
contracts, evidence identity or returned counts. A filtered graph is not used as
the denominator for impact percentages. Larger graphs still need zoom, focus or
the keyboard alternative list; Fit View cannot make every label readable at once.

## Verification

Commands use Node 22.14.0 with the existing npm CLI and the local backend/preview.
Final command results and manual screenshots are recorded with this handoff.
Browser fixtures are explicitly DEMO; manual QA uses the separate local test
account and real public TinyDB data. No paid provider or input-code execution is
needed for these UI checks.

The new browser cases check expanded graph width, collapsing/restoring panels,
retained file selection and impact, mobile transition from expanded mode, graph
zoom/Fit View and one initial snapshot acquisition with zero AI calls. Existing
loading, empty/error, import, theme persistence, print and representative AA text
contrast checks remain in the suite. Contrast checks are not a full WCAG audit.

The skill's dark reports probe at 375/768/1024/1280/1440px reports zero “Hỏng”. Its
remaining heuristics include expected signed-out 401, hidden native file input,
scrollbar parsing and uneven format-description row height. Probe logs are under
`var/nova-review-e0ccfa3c39/probe-reports-dark/`; none were silently discarded.

Known existing limitation: Vite warns about the large application chunk. This
change does not claim production deployment, performance benchmarks, hosted-user
acceptance, full backend testing or independent team review.

## Final verification and login/chart follow-up

The user's subsequent requests added direct theme toggling, reporting charts and
an improved login screen, followed by feedback to join the two login panes and
improve short-screen sizing, focus, pending and error states. Current behavior is
documented in `DESIGN.md`; historical screenshots describe earlier iterations.

New files: `features/auth/RepositoryArtwork.tsx`, `authPresentation.css`,
`features/projects/DashboardCharts.tsx`, `dashboardCharts.css`, and
`tests/login-charts.spec.mjs`, under `frontend/src` or `frontend/tests` as applicable.
The artwork is an inline SVG schematic, clearly captioned as an illustration;
there are no external image requests or added dependencies. Login data handling
retains the current authentication/CSRF transport and single-flight submission.

Reporting charts use existing `daily_runs`, `static_statuses`, `ai_statuses` and
filter/timezone fields. Calendar iteration includes zero days, respects the
exclusive end and handles DST without duplicating dates. A data table exposes
exact values; the range control supports keyboard date selection. The local QA
account's real snapshot currently contains zero runs; its empty state was
manually inspected. Nonempty charts were checked with explicit browser fixtures,
not claimed as live project results. Costs remain null/unknown where applicable.

Final checks from `D:\C1.SE26\Repo\frontend`, using Node 22:

- `npm run lint`: pass.
- `npm run build`: pass, includes TypeScript; existing large-chunk advisory remains
  (main JS about 757 kB uncompressed).
- `npm run contracts:check`: pass, 88 validation + 11 report SSR + 60 repository
  consumer + 20 authentication/transport checks.
- `npm run test:workspace`: **39 passed in 25.7s**. Includes 320–1440px login
  reflow, contiguous pane boundaries, 1440×900 / 1366×768 / 1280×720 / 1280×640
  no-clipping and form centering, keyboard/password/theme controls, disabled and
  pending login, credential vs infrastructure errors, reduced motion, chart
  sparse dates, exclusive end, DST, counts/percentages and empty states, plus
  existing workspace, import and theme cases.
- `git diff --check`: pass. No backend, schema, dependency or generated-contract
  changes in this follow-up. Earlier local edits remain present.

Browser screenshots at `var/login-charts-review-20261117/`:
`login-dark-desktop.jpg`, `login-light-desktop.jpg` (1366×768),
`login-dark-mobile.jpg`, `login-light-mobile.jpg` (375×900). Manual IAB inspection
also covered the real zero-run dashboard snapshot. Screenshots from the earlier
Nova pass are under `var/nova-review-e0ccfa3c39/screens/`; some early explorer
mobile full-page captures contain a browser capture/scroll artifact and are not
the final login evidence.

Backups: the original 134-file local-edit archive remains at
`var/nova-review-e0ccfa3c39/local-edits-before.zip`; the immediate login/chart
inputs are at `var/login-charts-review-20261117/before.zip`. No commit, push or
deployment was performed. Frontend and backend remain running locally.

Existing environmental limitation: GitHub metadata requests can hit its rate
limit; cached tree/graph/impact data remains available and the warning is retained.
The login changes and reporting charts do not require a GitHub request.
