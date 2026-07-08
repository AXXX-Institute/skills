# Reusing the shared `mls` library

The scaffolded launchers are **read-only consumers** of the shared `mls` CLI
library (installed in the environment; source at
`git+https://gitverse.ru/mrsndmn/mls@master`). Import its helpers instead of
re-implementing API access, job listing, or submission. **The skill never
modifies or pushes to `mls`** — treat it as an external dependency.

## Import surface (from `mls.manager.job.utils`)

| Symbol | Signature | Use |
|---|---|---|
| `training_job_api_from_profile` | `(profile_name) -> (client, {"region": ...})` | Build the API client + region from a named profile. |
| `get_in_progress_jobs` | `(client_profile='default', statuses=None, ...) -> list[dict]` | Pending+Running jobs; each dict has `job_desc`, `job_name`, `status`. Basis for dedup (pillar 3). |
| `run_job_with_retry` | `(client, payload, interval=60, verbose=True, profile=None) -> dict` | **Preferred submission.** Retries on `WORKSPACE_GPU_LIMIT_REACHED_ONLY_<n>_FREE`; registers in the local retry queue when `profile` is passed. Returns the API response (has `job_name` on success). |
| `filter_jobs_by_desc_glob` | `(jobs, pattern) -> list[dict]` | Filter jobs by `job_desc` glob/substring — handy for `killall`-style tooling. |
| `wait_for_job` | `(job_id, client_profile='default', poll_interval=5) -> bool` | Block until terminal; True on success. For synchronous flows. |
| `run_jobs_virtual_queue` | `(jobs_list, total_gpus=8, ...) -> dict` | Local virtual scheduler: submit a batch respecting a GPU cap, polling until slots free. Use when you want throttled batch submission instead of fire-and-forget. |
| `job_gpus_required` | `(payload) -> int` | GPUs a payload needs (parsed from `instance_type` × `n_workers`). |

Terminal-status constants also live here: `FINAL_JOB_STATUSES`,
`SUCCESS_JOB_STATUSES`.

## Minimal submission pattern

```python
from mls.manager.job.utils import (
    training_job_api_from_profile,
    get_in_progress_jobs,
    run_job_with_retry,
)

client, extra = training_job_api_from_profile("default")
in_progress = {normalize_job_desc(j.get("job_desc", "")) for j in get_in_progress_jobs()}
# ... build payload, dedup against in_progress ...
result = run_job_with_retry(client, payload, profile="default")
job_name = result.get("job_name")
```

## Payload shape (`type: "binary_exp"`)

```python
payload = {
    "script": "<shell to run inside the container>",
    "job_desc": "<emoji desc> #author @nick",
    "env_variables": {"HF_HOME": ..., "HF_TOKEN": ..., "WORKDIR": staged_workdir},
    "instance_type": "a100plus.1gpu.80vG.12C.244G",   # from `mls job instance_types`
    "region": extra["region"],
    "type": "binary_exp",
    "shm_size_class": "large",   # multi-GPU DataLoader needs big /dev/shm
    "base_image": "cr.ai.cloud.ru/aicloud-base-images/py3.12-torch2.7.0:0.0.41",
    "n_workers": 1,
    "processes_per_worker": 1,   # accelerate/torchrun own process spawning
    # "priority_class": "low",   # optional MLSpace scheduling priority
}
```

## Discovering instance types (do this live, per allocation)

Never hard-code the instance-type map without checking. Run:

```bash
mls job instance_types
```

It prints the exact `Тип инстанса` strings **available in the user's
allocation** (with free-GPU counts). Copy the relevant `Nxgpu` rows into the
launcher's `INSTANCE_TYPES_BY_NUM_GPUS`. The names differ by RAM tier (e.g.
`…12C.182G` vs `…12C.244G`), so pick the tier the allocation actually offers.

**`INSTANCE_TYPES_BY_NUM_GPUS` is project-specific — never import it from `mls`.**
Allocations expose different instance types and RAM tiers, so a shared library
must not pin them. Define the map once in the target repo's **`experiments.py`**
(alongside the experiments-as-code — the single per-project source of truth) and
have both `run_train_jobs.py` and `run_eval.py` import it from there, so it stays
DRY *within* the project without leaking allocation assumptions into `mls`.
Populate it from the live `mls job instance_types` table at scaffold time rather
than shipping a generic default.

## Optional shared `mls` helpers (import if present)

If the environment's `mls` install exposes these modules, prefer importing them
over the inline copies in the templates (they are the same logic hoisted into
`mls` so tracks don't each maintain a copy). All are pure/side-effect-light and
carry no allocation-specific data:

| Module | Exports | Replaces inline |
|---|---|---|
| `mls.manager.job.staging` | `stage_repo`, `git_toplevel`, `git_commit_hash`, `git_dirty_tracked` | the git-staging block |
| `mls.manager.job.dedup` | `normalize_job_desc`, `in_progress_descs` | job-desc dedup |
| `mls.manager.job.redact` | `redact_env`, `redact_payload` (both take an optional `hints` kwarg overriding `DEFAULT_SECRET_HINTS`) | `--dry` secret masking |
| `mls.manager.job.uv_env` | `uv_lock_hash`, `ensure_shared_venv` | shared-venv provisioning (uv repos only) |
| `mls.manager.job.notify` | `send_jobs_summary` | Telegram summary |

The templates keep inline fallbacks so a scaffold works even where these
modules aren't installed — if you wire the imports, guard them with a
try/except that falls back to the inline helper.

## Multi-GPU note

For `accelerate`/`torchrun`, keep `n_workers: 1` and `processes_per_worker: 1` —
the launcher owns multi-process spawning. If MLSpace *also* spawned processes
they would conflict. Combine with `shm_size_class: "large"` to avoid the
"No space left on device" `/dev/shm` error from DataLoader workers.

## The skill never modifies `mls`

The scaffolded launchers only *import* from `mls`. Adding to or changing the
`mls` library is a **separate, human-driven change** to the `mls` repo, made
deliberately — not something the skill does at scaffold time. Allocation-
specific data (instance types, regions, artifact roots) stays in the target
project, never in `mls`.
