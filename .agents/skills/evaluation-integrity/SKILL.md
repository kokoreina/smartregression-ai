---
name: evaluation-integrity
description: Use when planning SmartRegression datasets, baselines, fault labels, selection metrics, benchmark runs, or research claims.
---

# Evaluation integrity

Read `docs/research/evaluation-protocol.md` and rule 11 before designing or reporting
an experiment. Keep product correctness tests separate from method evaluation.

1. Freeze repository/commit pairs, inventory, cohort/split, configuration, method,
   baseline, environment and exclusions before the run. Record provenance and license.
2. Persist the proposed selection before running tests or joining outcomes. Selector
   inputs must not contain full-suite outcomes, fault labels or future information.
3. Separate verified real faults, mutation faults, flaky tests and infrastructure
   failures. A failing test is not itself a fault label; multiple failures may map to
   one independently adjudicated fault.
4. State numerator, denominator, zero-denominator policy, aggregation and time boundary.
   Unknown values remain null/N/A; preserve negative savings and failed/excluded runs.
5. Label illustrative/demo data. Never present targets, mock numbers or planned metrics
   as measured results. Report uncertainty, exclusions and threats to validity.

Project source: Proposal v1.4, Architecture v1.3 and `docs/research/evaluation-protocol.md`.
External method reference: GitHub Awesome Copilot skill format/progressive disclosure
(`docs/README.skills.md`), MIT repo, `main` (not commit-pinned); no content copied.
