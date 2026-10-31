# 1.01/1.11 — Primary source audit, 2026-10-24

Codex assisting Nguyen Tan Huy; paraphrases, no imported paper text or benchmark
numbers. Source checking is not independent human review of our protocol.

| Primary source read | Portion and supported use | Limits |
| --- | --- | --- |
| Gligoric, Eloussi, Marinov, [Ekstazi: Lightweight Test Selection](https://mir.cs.illinois.edu/~marinov/publications/GligoricETAL15EkstaziDemo.pdf), ICSE demo 2015 | Abstract/introduction describe dynamic file dependencies and integration; motivates a structural comparator and accounting for end-to-end cost | Java/JVM context; our static Python import spike is not Ekstazi and inherits no safety or performance results |
| Rothermel, Harrold, [A Safe, Efficient Regression Test Selection Technique](https://www.cs.purdue.edu/homes/xyzhang/spring07/Papers/p173-rothermel.pdf), TOSEM 6(2), 1997 | Abstract states safety under specific conditions using control-flow-based selection; motivates declaring assumptions before claims | Our incomplete AST/LLM design has no such proof; empirical retention does not establish universal safety |

Only the named sections were inspected for these claims, not a systematic literature
review or reproduction of either tool. These sources motivate RQs/baselines; the
proposed hybrid/no-RAG comparison is our protocol design, not a finding of these papers.

Local Proposal v1.4 §11.4 text was checked: target >=2 repos, >=30 pairs, >=15 verified
fault-bearing cases; model methods three repeats where budget permits, deviations
reported; impact unit functions/methods, independent labels and disagreement review.
Project Plan v1.1 uses 50 pairs. Group/mentor must reconcile scope/budget before
held-out runs; these planning requirements are not collected dataset/results.

Product behavior sources: [Git diff](https://git-scm.com/docs/git-diff),
[Python AST](https://docs.python.org/3.14/library/ast.html),
[pytest invocation](https://docs.pytest.org/en/stable/how-to/usage.html),
[pytest exit codes](https://docs.pytest.org/en/stable/reference/exit-codes.html),
[Docker limits](https://docs.docker.com/engine/containers/resource_constraints/).
Read for spike design; runtime evidence is recorded separately in the handoff.
