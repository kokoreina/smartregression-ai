# Sprint 1 — scope, decisions and acceptance checkpoints

## Current closeout decisions — 2026-11-08

Baseline: fetched `origin/main` at `3ab7d6603a191e46ce86d3ca04ffb520374bc639`.
Nguyen Tan Huy takes over remaining Sprint 1 work and authorized sequential
execution of the three closeout prompts: checklist/policy, verification, then
review/demo and Sprint 1 workbook synchronization. Historical authorship remains.
Follow-up authorization on 2026-11-08: Huy explicitly confirmed Done and requested
all three publication steps: update acceptance, commit/push/PR, then merge after
checks. This supersedes the earlier no-publication restriction; no mentor approval,
fabricated independent review or ruleset bypass is authorized.

| Item | Current decision / evidence | Boundary |
| --- | --- | --- |
| Scope | Research foundation + technical spike, 1.01–1.12/G1 | Not production PB01–04/PB23, dataset enrollment or Sprint 2–3 implementation |
| 1.06 | A01 accepted specification in [revision semantics](revision-semantics.md) | Live PR resolver, race handling and durable lifecycle are separate implementation |
| Candidates | D15 accepts fixed sqlparse primary and TinyDB backup; [source](../../development/task-2.08-2.09-decisions.md) | Reuse fixed snapshots for Sprint 1 reproduction, not a labeled research cohort |
| 1.10 | Huy authorizes final design `s1-selection-v1`, [policy](selection-policy.md) | No production selector, model call or empirical safety claim |
| Previous integration | [PR #13](https://github.com/kokoreina/smartregression-ai/pull/13) merged 2026-10-31, merge `0e79079649e3f508b534098b867d5ead4bb21ff6`; KaiTrann APPROVED | Fetched main contains that merge; review applies to PR revision, not today's changes or whole sprint |
| Sprint acceptance | Huy's explicit Done confirmation, 2026-11-08: 12/12 tasks Done | Bounded Sprint 1 scope; not mentor approval or production feature acceptance |
| Current delivery | Publish from the isolated main clone; [review/checklist](review.md) records verification and acceptance | Merge requires CI and actual GitHub rules; self-review is not independent approval |
| Workbook | Update Sprint 1 in local renamed workbook and repository's existing `_v1.4.xlsx` | Preserve forecast effort as estimates and actual-hour logs; do not copy local Sprint 2 changes onto main |

The sections below preserve the **2026-10-31 decision snapshot**. Their pending
candidate/specification/integration wording is superseded by the current table.
Future-stage design decisions still require their own implementation evidence.

## Historical closeout brief — 2026-10-31

Prepared by Codex assisting the user; not approval on behalf of owners or mentor.

## Scope authorized in this task

The user's current brief authorizes completing research foundation + technical
spike tasks 1.01–1.12/G1 locally, preserving current work, using public source
inspection and isolated candidate experiments. It excludes commits/push/PR merge,
GitHub settings, sub-agents, production pipeline/provider/DB and Office workbook
edits. That resolves the spike-versus-feature ambiguity for this implementation
task only. It does not resolve team capacity, calendar or mentor acceptance.

Publication follow-up 2026-10-31: the user subsequently authorizes a commit and
push of the prepared branch for their manual merge. Only those publication limits
are superseded; no main merge, approval or sprint acceptance is delegated.

Baseline main observed from GitHub: `e937f669fefada31d5254b355f92f24e88e41725`.
Starting checkout: `c3ac49aba58b9f50f933dc0b02aead28ee3d4217`; its tree matches
merged PR #10 `b37d1086af2f73882dcdf3367da40fe46fbcdd69`. PR #10 targeted the
technical feature branch after PR #9 entered main. Its research/RAG changes are
therefore included in this local handoff but not yet on remote main.

## Revision semantics

The detailed definitions remain in [1.06](revision-semantics.md). The source
requirement PR merge-base → head is described there; the adapter implements only
direct two-tree comparisons. Draft approval in PR #5 is recorded evidence of review,
not an explicit decision changing each proposed item to accepted.

| ID | Current evidence / bounded behavior | Decision still needed and when |
| --- | --- | --- |
| Q01 | User authorizes this closeout scope; PR #5 approved by kokoreina | Owner/consumer acceptance of final PR semantics before PR ingestion; final changed docs need review |
| Q02 | LocalGit receives authorized local repo and two full SHAs; does not acquire/resolve PRs | Writer/port for acquisition and resolver before implementing either |
| Q03 | Regex and commit-object checks; base=target returns no changes; direct diff does not require ancestry | Mutable ref/tag input contract and SHA-256 runtime support before promising them |
| Q04 | PR design proposes exactly one merge-base; insufficient history/no/multiple merge-base must stop | Accept this fail-closed proposal before resolver code; never silently substitute direct diff |
| Q05 | Immutable reads use supplied SHAs even with dirty working tree | Metadata race detection/freeze transaction before live PR ingestion; new head must create a new run |
| Q06 | ChangedComponent mapping records previous_path; deleted source reads base, runnable inventory reads target | Consumer approval before integrated report/PR provenance; no public schema extension in this task |
| Q07 | Adapter uses 50% rename similarity and rejects unsupported modes/paths | Broader path/binary/LFS/copy policy before expanding input support; no universal rename guarantee |
| Q08 | Bounded Git arguments, no textconv/hooks; synthetic fixture tests and candidate resource policy documented | General runner/isolation acceptance before arbitrary repositories; candidate scope stays two fixed snapshots |
| Q09 | Internal evidence can identify repo/actual diff pair; public schema lacks full PR metadata | Persistence/public metadata contract before exposing PR provenance |
| Q10 | In-memory Run rejects same-state transitions and terminal reopen; retry creates new UUID | Durable deduplication, stale/cancel/CAS and refresh semantics before production job service |

Recommendation for An/Huy and consumers: accept the definitions in 1.06 as the PR
resolver baseline, explicitly adopt fail-closed Q04/Q05 and assign resolver ownership.
No approval has been entered here. The two-full-SHA spike can be evaluated as its
documented subset; Q04/Q09/Q10 do not imply live PR support was delivered.

## Policy and experiment checkpoints

| Item | Source / recommendation | Needed by / effect now |
| --- | --- | --- |
| Python + pytest | Accepted in ADR 0002 | Already decided; input plugin/version matrix remains bounded by measured snapshots |
| Invalid evidence affecting selection | Proposal §12.6 says full suite, or stop when execution prerequisites fail; aligned 1.10/RAG drafts | Final design review; not a claim that production selector exists |
| Candidate choice | sqlparse primary and TinyDB backup proposed for spike; [runtime evidence](candidate-reproduction.md) | Owner confirms candidate acceptance before dataset enrollment; failed candidates stay visible |
| Dataset target | Proposal §11.4: ≥2 repositories, ≥30 pairs, ≥15 verified fault-bearing cases; Project Plan uses 50 pairs | Group/mentor reconciles before final sampling; no final dataset or fault labels required by current spike scope |
| Model/provider/budget | No paid calls or provider selected here | Before model pilot; not a blocker for offline scope/RQ/protocol docs |
| Pilot and held-out | Freeze identities/split before pilot tuning; freeze prompts/policy after pilot; held-out never used for tuning | Before experiments, not before synthetic/candidate reproducibility |
| Repeats/statistics | Proposal: three model trials where budget permits; record deviations and analysis unit | Freeze budget, repeats and intervals before held-out runs; none claimed measured |
| G1 snapshot materialization | Git blobs copied at frozen SHA instead of checkout; avoids filters/hooks | Reviewer assesses equivalence for the frozen-snapshot step; no live acquisition/PR race claim |
| Sprint acceptance | [Review](review.md) links all AC/evidence and remaining work | Human acceptance and integration into main remain separate from local technical readiness |

Design drafts may be technically ready while these future-stage decisions remain
pending. Any item affecting a required current AC stays a blocker and is not simply
renamed future work. Human review of new changes is not supplied by agent self-review.
