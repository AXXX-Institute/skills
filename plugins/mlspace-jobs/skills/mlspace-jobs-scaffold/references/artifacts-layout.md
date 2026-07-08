# Artifacts layout

## Principle

Artifacts live **outside the working directory**, referenced by a stable
**absolute path**. Code and outputs are separated: the repo is for source, the
artifacts root is for everything a job produces (weights, checkpoints, eval
JSONs) and everything a launch stages (code snapshots, venvs).

## The artifacts root: `/home/jovyan/<project_slug>-artifacts/`

The launchers reference a short, per-project path under the home directory:

```
/home/jovyan/<project_slug>-artifacts/
```

Normally this is a **symlink** to a larger/shared storage location the user
provides (e.g. an NFS mount with real capacity). The launcher code always uses
the clean `/home/jovyan/<slug>-artifacts/...` path for readability, while the
actual bytes live wherever the user has space:

```
/home/jovyan/myproj-artifacts  ->  /mnt/shared_<...>/myproj-artifacts
```

If the user has no separate storage — or prefers not to symlink — it can be a
plain directory at that path instead. Either way the launchers don't change; only
whether `/home/jovyan/<slug>-artifacts` is a symlink or a real dir differs.

## Choosing the symlink target (guess → confirm)

At scaffold time, decide the target **with** the user, don't assume:

1. **Guess.** Look for storage the user already uses and propose it as the target:
   - existing `*-artifacts` dirs/symlinks under `/home/jovyan/` (e.g.
     `/home/jovyan/myproj-artifacts`) and where they resolve to (`readlink -f`);
   - existing shared trees like `/mnt/shared_*/*-artifacts` or a project-specific
     NFS mount with free space.
   Prefer a sibling of an existing artifacts tree on the same storage
   (e.g. if `myproj-artifacts -> /mnt/shared_.../myproj-artifacts`, propose
   `/mnt/shared_.../<slug>-artifacts`).
2. **Confirm.** Ask the user via `AskUserQuestion`, offering:
   - **the guessed target** (recommended if one was found), or
   - **a custom target path** they type, or
   - **no symlink** — create a plain directory at `/home/jovyan/<slug>-artifacts/`.
   Never create the symlink/dir before this confirmation.
3. **Create.** Then either
   `mkdir -p <target> && ln -s <target> /home/jovyan/<slug>-artifacts`, or
   `mkdir -p /home/jovyan/<slug>-artifacts` for the no-symlink case.

## Tree beneath the root

```
/home/jovyan/<project_slug>-artifacts/            # symlink (or plain dir)
├── code/                          # staged code snapshots (pillar 4)
│   └── <commit_hash>/             #   one clean checkout per commit
├── venvs/                         # shared uv-lock venvs (optional pillar)
│   └── <uv_lock_hash>/
├── training/
│   ├── artifacts/                 # real training runs
│   │   └── <experiment_name>/
│   │       ├── config.json, model.safetensors, args.json
│   │       └── checkpoint-*/
│   │           └── evaluation/    # eval results co-located with the checkpoint
│   │               └── <dataset>.json
│   └── artifacts_sanity_check/    # sanity/CI runs — never collides with real runs
└── evaluation/
    └── data/                      # preprocessed eval datasets (inputs)
```

## Why co-locate eval results with checkpoints

Evaluation is **checkpoint-scoped**: results live under
`<checkpoint>/evaluation/<dataset>.json`, next to the weights they describe —
not in a central results directory. This makes the idempotency check (pillar 2)
trivial and keeps a checkpoint's scores from ever being attributed to the wrong
run.

## Placeholders the scaffold fills in

| Placeholder | Meaning | Example |
|---|---|---|
| `{{ARTIFACTS_ROOT}}` | training runs root | `/home/jovyan/<slug>-artifacts/training/artifacts` |
| `{{ARTIFACTS_ROOT_SANITY}}` | sanity/CI runs root | `/home/jovyan/<slug>-artifacts/training/artifacts_sanity_check` |
| `{{STAGING_ROOT}}` | staged code snapshots | `/home/jovyan/<slug>-artifacts/code` |
| `{{HF_HOME}}` | shared HF cache on NFS | `/mnt/shared_<...>/.cache/huggingface` |

All four are absolute and derived from the single `/home/jovyan/<slug>-artifacts/`
root — so the symlink (or plain dir) is the one thing that decides where the
bytes actually live.
