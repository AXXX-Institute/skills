# AXXX-Institute / skills

AXXX-Institute's [Claude Code](https://claude.com/claude-code) **marketplace** of
plugins. Each plugin lives under `plugins/<name>/` and ships one or more skills
under `plugins/<name>/skills/<skill>/`. The two plugins are **installable
independently**; the repo is built to grow — more AXXX plugins can be added the
same way.

## Plugins & skills

| Plugin | Skill | What it does | License |
|---|---|---|---|
| [`paper-to-poster`](plugins/paper-to-poster/) | [`paper-to-poster`](plugins/paper-to-poster/skills/paper-to-poster/) | Turn a paper into an **AXXX-branded** print-ready conference poster (single HTML/CSS → PDF), with affiliation logos pulled from this repo's asset releases. Ported from [posterly](https://github.com/Chenruishuo/posterly). | AGPL-3.0 (see below) |
| [`mlspace-jobs`](plugins/mlspace-jobs/) | [`mlspace-jobs-scaffold`](plugins/mlspace-jobs/skills/mlspace-jobs-scaffold/) | **Build** experiments-as-code MLSpace training + eval launchers (`run_train_jobs.py` / `run_eval.py` / `experiments.py`) into a repo — out-of-workdir artifacts, idempotent + in-progress-dedup submission, code staging; verified by a green `--dry` run. | MIT |
| [`mlspace-jobs`](plugins/mlspace-jobs/) | [`mlspace-jobs-quick-start`](plugins/mlspace-jobs/skills/mlspace-jobs-quick-start/) | **First-time** MLSpace setup: an interactive, one-step-at-a-time walkthrough from conda env → `mls` install → credentials → submitting and monitoring a first job. **Explicit-only** — launch it deliberately with `/mlspace-jobs-quick-start` (not auto-invoked, since it creates envs and installs packages). | MIT |
| [`mlspace-jobs`](plugins/mlspace-jobs/) | [`mlspace-jobs`](plugins/mlspace-jobs/skills/mlspace-jobs/) | **Operate** MLSpace once `mls` is configured: a command reference for monitoring, logs, waiting, killing jobs, `accelerate` multi-GPU config, and troubleshooting. | MIT |

## Installation

This repo is a Claude Code **marketplace** (`.claude-plugin/marketplace.json`)
that hosts two plugins. Install whichever you want, independently. If you install
`paper-to-poster`, also install its **runtime dependencies** (last subsection).

### Method A — Claude Code plugin marketplace (recommended)

In a Claude Code session, add this repo as a marketplace, then install either or
both plugins:

```
/plugin marketplace add AXXX-Institute/skills
/plugin install paper-to-poster@axxx-institute   # the poster builder
/plugin install mlspace-jobs@axxx-institute       # the MLSpace job skills
```

- `axxx-institute` is the marketplace name (from `marketplace.json`);
  `paper-to-poster` and `mlspace-jobs` are the two plugins.
- **Install only what you need** — the two plugins are independent. Installing
  `mlspace-jobs` does **not** pull in `paper-to-poster` (or its Playwright/Chromium
  runtime deps), and installing `paper-to-poster` does not pull in the MLSpace
  skills. Run just the one `/plugin install …` line you want.
- Installing a plugin exposes **all** skills it bundles — `mlspace-jobs` brings
  all three `mlspace-jobs*` skills; `paper-to-poster` brings the one poster skill.
- Update later with `/plugin marketplace update axxx-institute`; remove a plugin
  with `/plugin uninstall <plugin>@axxx-institute`.
- List/enable from the picker with `/plugin`.

### Ask an agent to install it (natural language)

Hand Claude Code the repo URL and say which plugin you want — it will add the
marketplace and install just that one:

> **https://github.com/AXXX-Institute/skills** — install the **mlspace-jobs** skills

> **https://github.com/AXXX-Institute/skills** — install the **paper-to-poster** skill

Under the hood the agent runs `/plugin marketplace add AXXX-Institute/skills`
followed by `/plugin install <plugin>@axxx-institute` — nothing else is installed.

### Method B — Manual copy (works in any setup, no marketplace)

A skill is just a directory containing `SKILL.md`. Clone the repo and drop the
skill dirs you want into a Claude Code skills directory:

```bash
git clone https://github.com/AXXX-Institute/skills.git axxx-skills

# Project-local (available in one project): from your project root
mkdir -p .claude/skills

# the poster builder:
cp -r axxx-skills/plugins/paper-to-poster/skills/paper-to-poster .claude/skills/paper-to-poster
# the MLSpace job skills (all three):
cp -r axxx-skills/plugins/mlspace-jobs/skills/* .claude/skills/

# Global (available in every project): copy into ~/.claude/skills/ instead
mkdir -p ~/.claude/skills
cp -r axxx-skills/plugins/paper-to-poster/skills/paper-to-poster ~/.claude/skills/paper-to-poster
```

Claude Code discovers skills in `.claude/skills/` (project) and `~/.claude/skills/`
(global) automatically — no restart needed for a new session.

### Method C — Lockfile (for repos using a skills-sync tool)

Pin a single skill in another repo's `skills-lock.json`:

```json
{
  "version": 1,
  "skills": {
    "paper-to-poster": {
      "source": "AXXX-Institute/skills",
      "sourceType": "github",
      "skillPath": "plugins/paper-to-poster/skills/paper-to-poster/SKILL.md"
    }
  }
}
```

See [`skills-lock.example.json`](skills-lock.example.json).

### Runtime dependencies (only for `paper-to-poster`)

`paper-to-poster` renders posters with headless Chromium and processes images, so
its tools need Playwright + Chromium (and Pillow for figure/logo handling):

```bash
pip install playwright pillow
playwright install chromium
```

Without these, the skill's `tools/poster_check.py measure` and
`tools/render_preview.py` fail. The `mlspace-jobs` plugin has no such runtime
dependency (it drives the `mls` CLI, which the quick-start skill installs).

### Using it

Once installed, just ask Claude in a session — e.g. *"make an AXXX poster for this
paper"* (activates `paper-to-poster`, workflow in
`plugins/paper-to-poster/skills/paper-to-poster/SKILL.md`), or *"set up MLSpace
training jobs in this repo"* / *"help me set up MLSpace for the first time"*
(activates the matching `mlspace-jobs` skill). Each skill activates from its
description.

## Licensing

The repo uses **per-plugin license isolation** — each plugin is its own
directory, so a copyleft plugin can't relicense a permissive one:

- **Repo scaffolding & docs (root):** **MIT** (`LICENSE`) — the marketplace
  manifest, README, gallery workflow, and repo tooling.
- **`paper-to-poster` plugin:** **AGPL-3.0**
  (`plugins/paper-to-poster/skills/paper-to-poster/LICENSE`, attribution in the
  adjacent `NOTICE.md`) because it derives from
  [posterly](https://github.com/Chenruishuo/posterly). AGPL is confined to that
  plugin directory; it is **not** relicensed by the MIT root.
- **`mlspace-jobs` plugin:** **MIT** — original work with no upstream; covered by
  the repo-root MIT license (declared in the plugin manifest), no separate
  per-skill `LICENSE`.
- **Future plugins** that derive from copyleft upstreams carry their own `LICENSE`
  inside their plugin directory; original plugins stay under the MIT root.

The permissive MIT plugins/root and the copyleft AGPL plugin coexist precisely
because AGPL is confined to its own directory. See
[`docs/adr/0003`](docs/adr/0003-agpl-license-isolation.md) and
[`docs/adr/0005`](docs/adr/0005-multi-plugin-marketplace-split.md).

## Asset releases

Affiliation logos and brand graphics are published as versioned **GitHub release
assets** (tag `assets-v1`). The `paper-to-poster` skill fetches the logos it needs
from a pinned tag and commits a copy into each poster repo, so posters render
offline and on Pages with no remote images. See
[`docs/RELEASE-assets.md`](docs/RELEASE-assets.md) and
[`docs/adr/0002`](docs/adr/0002-logo-delivery-releases-fetch-commit.md).

## Examples gallery

The four posterly examples, re-rendered in AXXX style, are published to GitHub
Pages: **https://axxx-institute.github.io/skills** — built from
[`plugins/paper-to-poster/skills/paper-to-poster/examples/`](plugins/paper-to-poster/skills/paper-to-poster/examples/)
by `.github/workflows/pages.yml`.

## Repo docs

- `CONTEXT.md` — glossary of domain terms.
- `docs/adr/` — architecture decision records.
