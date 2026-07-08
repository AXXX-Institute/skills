# 4. MLSpace job skills are migrated as three separate skills, not merged

- Status: accepted
- Date: 2026-07-08
- Component: #skills-repo scaffold (new MLSpace skills)

## Context

Three MLSpace job skills exist in sibling repos and are being migrated into the
`AXXX-Institute/skills` plugin:

- `mlspace-jobs-scaffold` (from `arkhip`) — **BUILD**: scaffolds
  experiments-as-code training/eval launchers (`run_train_jobs.py`, `run_eval.py`,
  `experiments.py`) into a target repo. Ships templates and reference docs.
- `mlspace-jobs` (from `occ-pipeline`) — **OPERATE**: a CLI command reference for
  the already-configured user (monitor/logs/wait/kill, accelerate multi-GPU,
  troubleshooting).
- `mlspace-jobs-quick-start` (from `occ-pipeline`) — **SETUP**: an interactive
  first-time walkthrough (conda env → mls install → credentials → first job
  lifecycle), task-tracked.

The question was whether to keep them separate, merge all three, or merge a
subset (a proposed option: merge `scaffold` + `mlspace-jobs`, keep `quick-start`
separate).

Analysis of overlap: `quick-start` is effectively `mlspace-jobs` **plus** setup
and hand-holding — its troubleshooting and accelerate sections duplicate
`mlspace-jobs` near-verbatim, and their eval prompts overlap. `scaffold` is
orthogonal: it is a code generator whose own description explicitly disclaims the
operate use case. So the genuine content overlap is `quick-start` ↔ `mlspace-jobs`,
**not** `scaffold` ↔ `mlspace-jobs`.

## Decision

Migrate all three as **separate skills** under `skills/<name>/`, keeping their
existing names. Do not merge.

- Each skill has a distinct, non-overlapping trigger — BUILD launchers /
  first-time SETUP / OPERATE commands — which routes cleanly via Claude Code's
  description-based skill activation.
- The proposed "merge `scaffold` + `mlspace-jobs`" option was **rejected**: it
  would combine the two most *different* skills (BUILD vs OPERATE, muddy trigger)
  while leaving the two most *similar* ones apart — backwards from where the
  duplication actually is.
- Content is ported with occ-pipeline-specific identifiers genericized
  (`#occ`/`#rnd` example tags removed; "occ-pipeline"/"OCC pipeline" provenance
  softened to neutral wording); commands, templates, the `mls` install source,
  and evals are preserved verbatim.
- These skills are **original work** (no upstream LICENSE in either source repo),
  so they are covered by the repo-root **MIT** license — no per-skill LICENSE,
  unlike the AGPL `paper-to-poster` (see ADR 0003).

## Consequences

- Clean routing: a first-timer, an operator, and someone bootstrapping launchers
  each hit exactly one skill.
- The small troubleshooting/accelerate duplication between `quick-start` and
  `mlspace-jobs` is accepted as the cost of clean triggers and cheap context
  (a command lookup should not load a 290-line interactive walkthrough).
- Reversible if it proves too granular: a later merge of `quick-start` +
  `mlspace-jobs` (with progressive disclosure via `references/`) remains open, and
  would dedup the overlap without touching `scaffold`.
- The MIT-root / AGPL-skill isolation from ADR 0003 is reaffirmed: original MIT
  skills coexist with the confined AGPL `paper-to-poster`.
