# Account, signout and impact presentation

Local changes on `feat/web-uiux-project-workspace` in `D:\C1.SE26\Repo`,
2026-11-17. Continues the Nova UI and login/chart handoff. Existing unpushed
work was retained; immediate inputs are backed up under
`var/account-impact-review-20261117/before.zip`.

## Findings and choices

The account's verified badge inherited the old light-only
`.status-pill.verified` background from `account.css`. `themes.css` now overrides
both its foreground and background with semantic tokens. Informational form
notices also use themed surfaces. Desktop account actions and feature search
no longer stretch the filled button across the entire panel.

Signout gets an optional presentation in the existing `ConfirmDialog`, rather
than another modal implementation: rounded neutral surface, session icon, close
button, explanatory text, Stay and a tinted signout action. Existing native modal
behavior, initial cancel focus, keyboard trapping, Escape and focus restoration
remain. Labels/descriptions use unique React IDs so simultaneous confirmation
instances do not duplicate the old `confirm-title` ID. Actual logout still uses
the existing cookie/CSRF single-session API.

More charts are not automatically better for this product. Chosen mapping:

| Place | Visual and purpose |
| --- | --- |
| Overview | Existing daily counts and static/AI status charts; new visible `Xem biểu đồ` entry uses the selected filters and existing reporting-view API. |
| Selected file | Horizontal comparison of changed/direct/indirect counts and percentages from `ImpactSummary`, keeping the analyzed-file denominator explicit. |
| Static propagation | Numbered path from `ImpactSummary.paths`, target selector and file actions; no invented edges or inference from diagram proximity. |
| Measured What-if overlay | Same comparison/path component, retaining total potential percentage and overlay qualifications. |
| Natural-language hypothesis | No static chart; the hypothesis disclaimer and existing AI action remain. |

No safety/risk gauges, fault probabilities, test pass rates, Sankey funnels or
global cross-project dependency graph were added: the existing data does not
support those interpretations. Import direction and impact-propagation direction
are explicitly distinguished. Unknown values stay unknown, coverage limitations
and truncated paths remain visible, and the full existing affected-file actions
remain available. These are display changes, not algorithm/contract changes.

## Verification

From `D:\C1.SE26\Repo\frontend`, Node 22:

- `npm run build`: pass, including TypeScript. Existing large-chunk advisory remains
  (about 760 kB main JS before gzip).
- `npm run lint`: pass.
- `npm run contracts:check`: pass: 88 validation, 11 report SSR, 60 repository
  consumer and 20 authentication/transport checks.
- `npm run test:workspace`: **46 passed in 26.4s**. Added coverage includes badge
  contrast and dark-surface luminance, modal cancel/close/Escape/focus/320px reflow,
  confirmed logout, explicit overview-chart request, exact impact counts, real
  path selection, unknown denominator, truncation, and overlay vs hypothesis.
- `git diff --check`: pass. Zero original files missing from the original
  134-file local-edit manifest.

Manual IAB checks use the separate local QA account, not the group's hosted
account. Real TinyDB snapshot `edff96aeb2616402e9489d46e90a592c05565621`, selected
`tinydb/table.py`, gives 1 changed, 3 direct and 7 indirect files out of 21. An
actual path to `tests/test_tables.py` is shown through `tinydb/database.py` and
`tinydb/__init__.py`. The 1,435 unresolved relations and 44 unsupported files stay
visible. No new snapshot, AI call or input-code execution was needed for this
presentation. Desktop dark account/signout/impact and mobile details were
inspected. Nonempty dashboard and What-if cases are browser fixtures, not live
project data or claims that a real What-if was executed during this UI task.

Screenshots: `var/account-impact-review-20261117/signout-dark.jpg`,
`account-dark.jpg`, `impact-context-dark.jpg`, `impact-mobile-dark.jpg`. The
context screenshot is the authoritative full viewport; `impact-path-dark.jpg`
is an earlier clipped capture and does not show the full propagation section.

No dependencies, backend, migrations or generated types changed. No commit,
push or deployment. Frontend/backend remain running locally. Existing GitHub
quotas and large-graph readability limits are not claimed fixed by this change.
