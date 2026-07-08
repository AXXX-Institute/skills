# The four pillars of a robust MLSpace launcher

These are the load-bearing patterns every scaffolded launcher reproduces. Each
exists to solve a specific failure mode observed on MLSpace. When you adapt a
template, preserve the *intent* of each pillar even if the mechanics change for
a given repo.

## 1. Out-of-workdir artifacts (absolute paths)

**Why:** MLSpace jobs run in an ephemeral container; the launch host's working
directory may be a GitLab-runner checkout that gets wiped between pipelines.
Writing outputs under the repo means losing them (or bloating git). Writing to
an **absolute path on shared NFS** keeps artifacts durable and reachable from
every node.

- Every run writes to `<ARTIFACTS_ROOT>/<experiment_name>/…`.
- Sanity/CI runs write to a **separate** root so they never collide with real runs.
- `/home/jovyan/<slug>-artifacts` is typically a symlink to a shared NFS tree
  (e.g. `/mnt/shared_<...>/<slug>-artifacts`) — prefer the `/home/jovyan/...` form
  in code for readability, but know they are the same tree. See
  `artifacts-layout.md` for the proposed layout.
- Mark finished runs read-only (`0444`/`0555`) if your entrypoint supports it, so
  a later job can't silently corrupt them.

## 2. Idempotent launches (skip-if-done)

**Why:** Re-running the launcher after a partial batch should only submit what's
missing — not duplicate completed work or clobber good outputs.

- Before submitting, check a **terminal marker** the entrypoint writes last
  (e.g. `training_metadata.json`, or all expected `<dataset>.json` eval results).
- If present → skip, unless `--force`.
- Keep the check cheap (a file `exists()`), and make the marker something that
  only appears on *successful completion*, never mid-run.

## 3. In-progress dedup (skip-if-queued)

**Why:** Idempotency (pillar 2) only catches *finished* work. A job that is
still `Pending`/`Running` has written no artifacts yet, so without this check a
second launcher invocation would submit a duplicate and waste the allocation.

- List active jobs via `mls`' `get_in_progress_jobs()` (statuses Pending+Running).
- Compare on a **normalized job description**: strip `#tags` and `@mentions` so
  the same experiment from different authors still dedups on its body.
- Encode the experiment's stable identity (its `name`) into the description so
  the match is exact and collision-free.

## 4. Code staging (clone to a separate dir)

**Why:** An MLSpace job may start minutes after you submit it, and you'll keep
editing your working tree meanwhile. If the job read code from your live
checkout, an unrelated edit could change what a running experiment executes —
irreproducible and dangerous.

- Refuse to submit when the tracked tree is **dirty** — staging materializes
  from `.git`, so uncommitted changes would be silently dropped. Fail loudly and
  tell the user to commit or stash.
- Stage to `<STAGING_ROOT>/<commit_hash>`: `cp -a .git` then `git reset --hard HEAD`.
  This is **idempotent** (reuse if the dir exists) and **atomic** (stage into
  `<target>.tmp.<pid>`, then `os.rename`). Two commits with the same hash share
  one stage.
- Only `.git` is copied, so gitignored `.venv`/build artifacts stay out; the
  checkout is a clean tracked tree at exactly that commit.
- The job `cd`s into the staged dir and sets `PYTHONPATH` there.

### Companion: shared venv by uv.lock hash (only if the repo uses `uv`)

If the target repo pins deps with `uv`, a job shouldn't `uv sync` on every node
(NFS `flock` is unreliable across MLSpace workers). Instead, sync **once** on the
submitter host into `<VENV_ROOT>/<sha256(uv.lock)[:16]>` and have the job export
that venv. Two commits with identical `uv.lock` reuse the same environment. Skip
this pillar entirely for pip/conda repos — explore the repo first and confirm.

## Identity, safety and observability knobs

- **`--author_name` / `--telegram_nick`** (required): tag every `job_desc` so
  humans and the dedup logic can attribute jobs.
- **`--dry`**: print the exact payload/script and submit nothing. This is the
  primary verification path — a scaffold is "done" when `--dry` prints correct
  payloads for both launchers.
- **`--force`**: override pillar 2 to intentionally re-run.
- **`--filter`**: substring-match experiment names to launch a subset.
- **JSON summary**: print a `__…_JOBS_JSON__` marker + one JSON line so an outer
  orchestrator can parse what was launched.
- Prefer `run_job_with_retry` over a raw `client.run_job` so a transient
  `WORKSPACE_GPU_LIMIT_REACHED` backs off and retries instead of failing.
