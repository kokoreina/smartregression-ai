# SmartRegression workspace

Design baseline: 2026-11-17, main `a55e44bc52eea22387c1d174f13d78eae80d2b99`.
The user delegated selection of the UI direction and implementation of the redesign.

## Product and main workflow

For developers and students exploring a public repository: projects → open project
→ inspect the snapshot tree → select a file → read static dependencies/impact and
evidence → optionally open a what-if or a saved analysis. Project administration
supports that workflow and must not hide the explorer behind settings/history.

The UI borrows the Nova references' inset workspace and neutral hierarchy, adapted
to a developer tool: labeled sidebar, flat work panels and a restrained teal accent.
The user asked to remove
the large green areas, simplify typography and make the sparse screens useful.
The SR monogram remains. No charts, stats, AI outputs, permissions or project
capabilities are invented for presentation.

## Shared controls

| Element | Convention |
| --- | --- |
| Buttons | 40px baseline, 44px report actions on mobile, 10px radius, one filled primary action per region; neutral secondary actions; 160ms color feedback and a 1px press response |
| Status | Compact text badge with a 6px radius; exact existing state labels |
| Inputs | 40px baseline, visible label, light border, distinct keyboard focus; full SHA retained |
| Panels | White flat surface, 12px radius, 24px padding; denser explorer panels use 18px |
| List rows | Entire real action has a clear hover/focus state; native file identity preserved |
| Dialogs | Existing ConfirmDialog; no decorative duplicate modal implementation |
| Empty/loading/error | Explain the specific missing input or failure and provide an existing next action |

Font is the native system sans stack, as requested by the user, overriding the
skill's default Inter. Names and source paths retain monospace where useful.
Color, radius, spacing, type and motion tokens for both modes live in
`frontend/src/app/design-tokens.css`. Layout lives in `workspace.css`; `themes.css`
bridges existing report/form components to the shared palette.
Visual rhythm is calm with emphasis on the current project and selected file.
Route fade animations are disabled. A loading indicator communicates real work;
reduced motion is respected. Light and charcoal dark palettes share the same layout
and meanings. The header's Giao diện button switches directly between light and
dark with one click, following the user's latest request. Before any explicit
choice, the OS preference applies. A manual choice is persisted locally.
`frontend/public/theme-init.js` applies the preference before React and styles
paint; `theme.ts` handles live OS changes and cross-tab synchronization.
Shared dark surfaces, semantic state colors, graph controls and print overrides
live in `frontend/src/app/themes.css`. Printing uses a light palette.

The sidebar has four real navigation items, an active-location marker and an
account area. The initial dashboard uses actual API projects and a saved-report
entry point instead of empty metric cards. A failed project request is distinct
from an empty list. Report import has a real drag/drop target, the supported
formats and a common toolbar after validation. It remains available signed out.
Work panels use stronger dividers than the skill's decorative-border default to
make the three adjacent explorer regions easier to distinguish.

Labels are Vietnamese, with technical identifiers preserved. The HTML language
remains `vi` and `translate="no"` plus the standard Google no-translation meta
flag discourage automatic translation from duplicating labels or changing paths.
Browser extensions that ignore these flags remain outside application control.

## Authentication and reporting follow-up

Authentication uses one continuous split layout with aligned, full-height panes,
without detached cards or a gutter between the story and form. The form stays
centered at up to 420px. Short desktop viewports simplify the illustration and
omit its redundant diff strip; mobile prioritizes the form and omits the artwork.
The dependency artwork is explicitly illustrative. Its brief node highlight plays
once and is disabled for reduced motion. Login fields use shared input-border,
focus and error tokens. Credential errors describe both fields; service failures
remain separate. Pending submits have a disabled action and progress indicator.

Dashboard charts consume the existing immutable reporting snapshot: daily run
counts, static processing statuses and AI processing statuses. Up to twelve days
use columns; longer intervals use a straight line. Missing calendar days in a
successfully loaded aggregation are zero; a wholly empty snapshot shows an empty
state. Counts remain accessible through a table and a keyboard day selector.
Static status is never presented as test pass/fail. No sample results are added
to production screens, and unknown provider cost remains unknown.

The verified account badge and notices use semantic theme tokens, including their
backgrounds. Account actions and feature search avoid wide filled buttons on
desktop. Signout retains the native confirmation dialog, with a neutral surface,
muted supporting text, a tinted action, close/Stay/Escape and return focus. It
does not change the session until confirmed.

Overview exposes a clear `Xem biểu đồ` action to load the existing filtered
reporting view. It does not start a new analysis. Project Explorer and measured
What-if overlays show horizontal impact comparisons against the backend's
analyzed-file denominator, together with real `ImpactSummary.paths` as a numbered
propagation chain. Missing counts/percentages remain unknown. A chain represents
one observed static route, in the reverse direction of imports; it is not a
runtime trace. Coverage/truncation limits stay visible. Natural-language
hypotheses get no measured chart. No risk score, safety gauge or sales-style
funnel is implied by these visuals.

## Layout and responsive behavior

Desktop: sidebar + project title/actions + project sections + snapshot toolbar +
tree/graph/inspector. At 1350px and below the inspector moves to its own row. At 768px
the explorer switches between Tree / Graph / Details, retaining selection in the
URL. At 900px the sidebar is opened with a labeled navigation toggle, supporting
Escape and closing when a navigation destination is chosen.

Desktop panels can collapse without unmounting notes/source state. Expanded graph
mode hides side panels and refits the canvas; selection still updates the same URL
and impact result. Opening Chi tiết file restores the inspector. Narrow screens
keep the existing three tabs, regardless of the desktop panel state.

The graph defaults to file-level dependencies; folders, symbols and edge labels
are explicit display options. Node ports follow the left-to-right Dagre layout.
The selected file is framed at a readable camera scale when focus is enabled;
Đến file đã chọn restores that camera, and Fit View remains available for overview.
No nodes, dependencies, impact counts or evidence are synthesized by these controls.

Project detail defaults to code exploration. First entry can resolve the latest
commit and materialize one bounded static snapshot after checking saved state.
Saved links only read cached snapshots until the user explicitly reloads one.
Tree, graph, node list and hotspot requests fail independently. No provider call,
dependency installation or input-repository execution is initiated by this flow.

## Skill provenance

UI conventions use the user-requested evondevKit `ui-ux` skill, vendored in
`.agents/skills/ui-ux` at upstream commit
`5a892ceac93d1bb286391663eb01cbd011706886`, MIT. The user explicitly asked the agent
to choose and improve the UI, so design direction is delegated rather than waiting
for the skill's default brief/wireframe approval sequence. Repo contracts,
functional behavior and accessibility take precedence over generic visual examples.

## Coverage explanation

Coverage separates syntax-read files, parse failures, unsupported file categories
and unresolved-reference occurrences across the entire snapshot. An expandable
breakdown distinguishes internal import gaps, possible external dependencies,
variable/dynamic calls and ambiguous symbols. Recognized Python built-ins and
standard-library references are counted separately and retain path/line records.
Old payloads without diagnostics show an explicit unavailable-breakdown message.
File grouping is a filename/extension aid, not proof that configuration changes
are harmless. The 150-node display bound stays distinct from parser coverage.
Conservative partial status is retained rather than changed for presentation.
