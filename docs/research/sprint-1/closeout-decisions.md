# Sprint 1 — scope, decisions and acceptance checkpoints

Updated 2026-10-31 by Codex assisting the user. This is a decision index and a
review proposal, not a new approval on behalf of task owners or mentor.

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
