# Glossary (CONTEXT.md)

Canonical domain terms for the **axxx-skills** repo — a Claude Code **marketplace**
hosting two independently-installable plugins (`paper-to-poster`, `mlspace-jobs`).
Glossary only — no implementation detail. See `docs/adr/` for decisions and the
skill sources for code.

## skills repo (AXXX-Institute/skills)
The public, org-owned Claude Code **marketplace repository**. Its root
`.claude-plugin/marketplace.json` lists **plugins**, each under `plugins/<name>/`
with its own `.claude-plugin/plugin.json` and skills at
`plugins/<name>/skills/<skill>/`. GitHub identity: **`AXXX-Institute/skills`**
(Pages at `axxx-institute.github.io/skills`, release assets at
`github.com/AXXX-Institute/skills/releases/...`); checked out locally as
`axxx-skills`. Ships `paper-to-poster` and `mlspace-jobs`; built so further
plugins can be added later.
_Avoid:_ "the poster repo" (that names the user's paper repo, not this one);
"axxx-skills" as the GitHub name (it's the local dir; the remote is
`AXXX-Institute/skills`); "the plugin" (singular — the repo is a marketplace of
several plugins).

## paper-to-poster
The skill ported from upstream **posterly** that turns a paper into a print-ready
conference poster, restyled so it **always** emits the AXXX brand look (no neutral
fallback). Keeps posterly's measure/polish gates and tooling.
_Avoid:_ "posterly" (that names the unmodified upstream skill we ported from).

## AXXX theme
The single, baked-in brand style the `paper-to-poster` skill always applies:
the AXXX `:root` token block (accent `#0689D4`, deep `#053957`, light-blue tints,
one semantic red), the **Inter** typeface, the top accent bar, arrow-glyph bullets,
and the affiliation logo set. There is no neutral/house-style fallback — the skill
is AXXX-only.
_Avoid:_ "neutral theme", "house style" (the upstream concepts we removed);
"palette derivation" (the upstream step we dropped).

## Affiliation logo
A brand mark for a contributing institution (AIRI, FusionBrain, HSE, Innopolis, …)
placed in the poster header. Maintained **centrally** as a versioned **GitHub
release asset** of `axxx-skills`; at build time the skill **fetches** the needed
logos from a pinned release tag and **commits the copy into the poster repo's
`images/`** so each poster is self-contained (offline render, Pages-deployable,
no remote `<img>`). Releases are the upstream-of-record; the poster vendors a
fetched copy. Upgrading = re-fetch a newer tag.
_Avoid:_ "venue logo" (that names the conference mark, a separate concept).

## Reference poster
`compression_horizon/poster/poster.html` — the hand-built, already-AXXX-styled
poster that is the canonical visual target for the AXXX theme.
_Avoid:_ "the template" (templates are the neutral posterly scaffolds).

## poster repo
The **user's own** project/paper repository in which the skill is invoked. The
skill writes the poster into `./poster/` here by default (mirroring
`compression_horizon/poster/`) and offers to add a Pages-deploy workflow.
_Avoid:_ "skills repo" (that is `AXXX-Institute/skills`, a different repo).

## assets release (assets-vN)
The versioned GitHub release of `AXXX-Institute/skills` that carries the
affiliation logo set (and bullet/QR marks). Tagged `assets-v1`, bumped on change;
the skill pins a tag and fetches from it. See [[affiliation-logo]].
_Avoid:_ "rolling tag" (a moving tag breaks the pinned-reproducibility contract).

## Pages gallery
The static GitHub Pages site of `AXXX-Institute/skills`
(`axxx-institute.github.io/skills`) that showcases the four posterly examples
re-rendered in AXXX style, listed by an `index.html`. Distinct from a single
poster repo's own Pages deploy.
_Avoid:_ "the demo" (the gallery is the published showcase, not a smoke test).

## MLSpace
The GPU compute platform (Cloud.ru) the job skills target: users submit **jobs**
to an **allocation**, picking an **instance type** for GPU/CPU/RAM. Driven from
the `mls` CLI. The three MLSpace skills split cleanly by job-to-be-done:
**BUILD** ([[mlspace-jobs-scaffold]]), first-time **SETUP**
([[mlspace-jobs-quick-start]]), and day-to-day **OPERATE** ([[mlspace-jobs]]).
_Avoid:_ "the cluster" (MLSpace is the managed platform, not a bare cluster).

## mls (CLI)
The command-line tool that talks to MLSpace (`mls job submit/table/status/logs/
kill/wait`, `mls job instance_types`, `mls configure`). Installed from
`git+https://gitverse.ru/mrsndmn/mls@master`; a **read-only** dependency of the
skills — never edited or pushed to from a skill. All three MLSpace skills operate
`mls`; [[mlspace-jobs-scaffold]] additionally imports its `mls.manager.job`
helpers into the launchers it generates.
_Avoid:_ "MLSpace SDK" (it's the CLI; the importable helpers are a sub-surface).

## mlspace-jobs-scaffold
The **BUILD** skill: scaffolds experiments-as-code training/eval launchers
(`run_train_jobs.py`, `run_eval.py`, `experiments.py`) into a target repo,
following four pillars — out-of-workdir artifacts, idempotency, in-progress
dedup, and code staging. Deliverable is diff-reviewable Python + a green `--dry`
run; it never launches a real job. Ships templates and reference docs.
_Avoid:_ "job runner" (it generates launchers, it does not run jobs);
"mlspace-jobs" (that is the OPERATE reference, a different skill).

## mlspace-jobs
The **OPERATE** skill: a CLI command reference for a user who **already** has
`mls` configured — monitor/logs/wait/kill, accelerate multi-GPU config, and
troubleshooting. No setup walkthrough.
_Avoid:_ "quick-start" (that is the first-time SETUP skill); "scaffold" (that is
the BUILD skill).

## mlspace-jobs-quick-start
The **SETUP** skill: an interactive, task-tracked, one-step-at-a-time walkthrough
for a **first-time** MLSpace user — create a conda env, install and configure
`mls`, submit and monitor a first job. Supersets [[mlspace-jobs]]' operational
guidance for the not-yet-configured user. **Explicit-only**: it sets
`disable-model-invocation: true`, so Claude never auto-launches it; the user runs
it deliberately with `/mlspace-jobs-quick-start` (it has side effects — creates
conda envs, installs packages, writes credentials).
_Avoid:_ "mlspace-jobs" (that is the reference for the already-configured user).
