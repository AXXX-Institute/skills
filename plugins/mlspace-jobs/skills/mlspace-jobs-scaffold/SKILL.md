---
name: mlspace-jobs-scaffold
description: >-
  Scaffold MLSpace distributed training AND evaluation job launchers into a
  repo — experiments-as-code, out-of-workdir absolute-path artifacts, idempotent
  + in-progress-dedup submission, and code-staging so live edits can't perturb
  running jobs. Use this WHENEVER the user wants to set up, add, generate, or
  bootstrap MLSpace job submission for a project: phrases like "set up MLSpace
  training jobs", "add run_train_jobs.py / run_eval.py", "launch training/eval on
  MLSpace", "submit jobs to my allocation", "experiments as code for MLSpace",
  "make my train.py runnable on MLSpace", or "port my existing job launchers
  to this repo". Reuses the shared `mls` library as a read-only dependency and
  discovers the allocation's instance types with `mls job instance_types`. This
  is for BUILDING the launchers, not for running one-off `mls job
  status/logs/kill` commands on an already-configured setup.
---

# MLSpace Job Scaffold

Bootstrap production-grade MLSpace **training** and **evaluation** launchers into
a target repo, following proven job-launcher patterns. The output is
diff-reviewable Python — experiments live as code, artifacts live outside the
working tree at absolute paths, and every launch is idempotent, dedup-safe, and
reproducible.

## What "done" looks like

A scaffold is complete when the target repo has:

1. `experiments.py` — an `ExperimentConfig` dataclass + a `collect_experiments()`
   registry with **≥1 concrete example experiment**.
2. `run_train_jobs.py` and `run_eval.py` — launchers that import `mls` helpers
   and implement the four pillars (below).
3. An artifacts-layout doc/section describing the out-of-workdir scheme.
4. **Both** `python run_train_jobs.py --dry` and `python run_eval.py --dry`
   print correct MLSpace payloads **without launching any job**.

No real GPU job is submitted. The green `--dry` run is the acceptance test.

## The four pillars (never drop one)

Every launcher must reproduce these. Full rationale in
`references/patterns.md` — read it before adapting the templates.

1. **Out-of-workdir artifacts** — absolute NFS paths, separate sanity root.
2. **Idempotency** — skip if a terminal artifact marker exists (unless `--force`).
3. **In-progress dedup** — skip if a job with the same normalized description is
   Pending/Running (via `mls`' `get_in_progress_jobs`).
4. **Code staging** — refuse a dirty tree, then `cp -a .git` + `git reset --hard`
   into `<STAGING_ROOT>/<commit>` so live edits can't change a running job.

## Workflow

Follow these steps in order. Prefer inferring facts from the repo over asking —
only ask what you genuinely cannot determine (matches the "gather facts before
asking" discipline).

### Step 1 — Explore the target repo

Determine, by reading the repo:
- **Training entrypoint** — a `train.py`, `scripts/train.py`, `-m pkg.train`, or a
  `trl`/`accelerate` invocation. Note whether it takes a config file or flags.
- **Evaluation entrypoint** — an `eval.py`/`scripts/eval.py`, or none yet.
- **Dependency manager** — `uv.lock` (→ enable the shared-venv companion),
  else pip/conda (→ skip it).
- **Package layout** — where importable code lives, so `PYTHONPATH`/imports are right.
- **Existing artifacts storage** — look for `*-artifacts` dirs/symlinks under
  `/home/jovyan/` and shared trees like `/mnt/shared_*/*-artifacts` (resolve
  symlinks with `readlink -f`). These are candidate targets for this project's
  artifacts symlink (see Step 3 and `references/artifacts-layout.md`).
- **Checkpoint format** — what a finished run writes last (the idempotency marker)
  and how checkpoints are named (`checkpoint-*`?).

### Step 2 — Discover instance types (live)

Run `mls job instance_types` and read the table of instance types **available in
the user's allocation** (see `references/mls-helpers.md`). Choose the `Nxgpu`
rows that match the RAM tier the allocation actually offers — do not hard-code a
generic map. Turn the discovered rows into a `{num_gpus: "<instance_type>"}`
dict; in Step 4 you write it into `experiments.py`'s `INSTANCE_TYPES_BY_NUM_GPUS`
(the single per-project source of truth both launchers import). If `mls` is not
configured, help the user set it up first (create an `mls` profile with their
allocation credentials) before scaffolding.

### Step 3 — Propose, then confirm

Present a short plan and get a yes/no with `AskUserQuestion` before writing files:
- the **artifacts root** — always `/home/jovyan/<project_slug>-artifacts/`, plus
  **where it points**: a symlink to a storage target (default to the one you
  guessed in Step 1), a custom target the user types, or **no symlink** (a plain
  dir at that path). See `references/artifacts-layout.md`. Show the four derived
  paths (`{{ARTIFACTS_ROOT}}` etc.) so the user sees exactly where bytes land.
- the chosen **instance-type map**;
- the **train/eval entrypoints** and launch mechanism (`accelerate` / `torchrun` / `python`);
- whether to enable the **shared-venv** companion.

State the defaults you inferred and let the user correct them. Ask outright only
for what you couldn't infer (e.g. GPU count per experiment, eval datasets).
Only after this confirmation, create the root:
`mkdir -p <target> && ln -s <target> /home/jovyan/<slug>-artifacts` (symlink), or
`mkdir -p /home/jovyan/<slug>-artifacts` (no-symlink).

### Step 4 — Generate the files

Copy the templates from `assets/` and replace every `{{PLACEHOLDER}}`:

| File | Template |
|---|---|
| `experiments.py` | `assets/experiments.py.tmpl` |
| `run_train_jobs.py` | `assets/run_train_jobs.py.tmpl` |
| `run_eval.py` | `assets/run_eval.py.tmpl` |

Placeholders: `{{PROJECT_NAME}}`, `{{PROJECT_SLUG}}`, `{{TRAIN_ENTRYPOINT}}`,
`{{EVAL_ENTRYPOINT}}`, `{{DEFAULT_MODEL}}`, `{{EVAL_DATASET}}`,
`{{ARTIFACTS_ROOT}}`, `{{ARTIFACTS_ROOT_SANITY}}`, `{{STAGING_ROOT}}`,
`{{HF_HOME}}`, and `{{INSTANCE_TYPES_BY_NUM_GPUS}}` (in `experiments.py` only —
replace it with the dict you built in Step 2). Set the `from experiments import …`
path to the repo's package layout. Both launchers import
`INSTANCE_TYPES_BY_NUM_GPUS` from `experiments.py`; do **not** reintroduce a
hardcoded map in the launchers. `repo_root` is resolved with
`git rev-parse --show-toplevel`, so the launcher works whether it sits at the
repo root or under `scripts/` — no manual edit needed. Write the artifacts-layout
section into the repo's docs or README.

Keep it minimal: **one** working example experiment beats a speculative sweep.

The templates are built to make `--dry` **side-effect-free and safe to share**:
they don't write the run config in dry mode (`write_config=not args.dry`) and
they print the payload with secrets masked via `mls.manager.job.redact.redact_payload`
(imported from `mls`, with a small inline fallback for older `mls`). The masked
key-substrings are overridable via its `hints` kwarg if the repo uses unusually
named secret vars. Preserve both behaviors when you adapt them.

### Step 5 — Verify with `--dry`

Run both launchers in dry mode from the repo:

```bash
python run_train_jobs.py --author_name <you> --telegram_nick <you> --dry
python run_eval.py --checkpoints_dir <ARTIFACTS_ROOT> --author_name <you> --telegram_nick <you> --dry
```

Success = each prints a well-formed job description + shell script + (secret-
masked) payload and submits nothing. Fix import errors, path errors, and
placeholder leftovers until both are green. Show the user the dry output. Do
**not** submit a real job unless they explicitly ask.

A **fresh** project legitimately has no `checkpoint-*` dirs yet, so
`run_eval.py --dry` reports "nothing to evaluate" and exits 0 — that is a green
result, not a failure. It becomes a real per-checkpoint dry run once training
has produced checkpoints.

## Constraints

- **`mls` is read-only.** Import from `mls.manager.job.utils`; never edit or push
  to the shared `mls` repo from this skill.
- **Absolute paths are environment-specific** — always confirm the artifacts root
  with the user before writing it into code.
- **Never launch a real job** as part of scaffolding. The deliverable is code +
  green `--dry`, nothing more.
- **Scope:** training + evaluation launchers only. Not reasoning-pipeline or
  synth-data launchers.

## Reference material

- `references/patterns.md` — the four pillars, in depth, with the failure mode each prevents.
- `references/artifacts-layout.md` — the proposed unified out-of-workdir layout + placeholders.
- `references/mls-helpers.md` — the exact `mls` import surface, payload shape, and instance-type discovery.
- `assets/*.tmpl` — the launcher + experiments templates to copy and fill.
