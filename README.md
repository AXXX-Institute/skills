# AXXX-Institute / skills

[![Docs — GitHub Pages](https://img.shields.io/badge/docs-axxx--institute.github.io%2Fskills-0689D4?logo=github&logoColor=white)](https://axxx-institute.github.io/skills/)

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

### Method A — Plugin marketplace (recommended)

Same marketplace, same two plugins, from **Claude Code** or **OpenAI Codex**.
Add this repo as a marketplace once, then install either or both plugins.

**Claude Code** — in a session:

```
/plugin marketplace add AXXX-Institute/skills
/plugin install paper-to-poster@axxx-institute   # the poster builder
/plugin install mlspace-jobs@axxx-institute       # the MLSpace job skills
```

**OpenAI Codex** — from your shell:

```bash
codex plugin marketplace add AXXX-Institute/skills
codex plugin add paper-to-poster@axxx-institute   # the poster builder
codex plugin add mlspace-jobs@axxx-institute       # the MLSpace job skills
```

- `axxx-institute` is the marketplace name (from `marketplace.json` /
  `.agents/plugins/marketplace.json`); `paper-to-poster` and `mlspace-jobs` are the
  two plugins. `AXXX-Institute/skills` is the GitHub `owner/repo` shorthand both
  tools accept.
- **Install only what you need** — the two plugins are independent. Installing
  `mlspace-jobs` does **not** pull in `paper-to-poster` (or its Playwright/Chromium
  runtime deps), and installing `paper-to-poster` does not pull in the MLSpace
  skills. Run just the one install line you want.
- Installing a plugin exposes **all** skills it bundles — `mlspace-jobs` brings
  all three `mlspace-jobs*` skills; `paper-to-poster` brings the one poster skill.
- **Update:** Claude `/plugin marketplace update axxx-institute` · Codex
  `codex plugin marketplace upgrade axxx-institute`.
- **Remove:** Claude `/plugin uninstall <plugin>@axxx-institute` · Codex
  `codex plugin remove <plugin>@axxx-institute`.
- **List / enable:** Claude `/plugin` · Codex `/plugins` (in-session) or
  `codex plugin list`.

### Ask an agent to install it (natural language)

Hand Claude Code the repo URL and say which plugin you want — it will add the
marketplace and install just that one:

> **https://github.com/AXXX-Institute/skills** — install the **mlspace-jobs** skills

> **https://github.com/AXXX-Institute/skills** — install the **paper-to-poster** skill

Under the hood the agent runs `/plugin marketplace add AXXX-Institute/skills`
followed by `/plugin install <plugin>@axxx-institute` — nothing else is installed.

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

## Documentation site (GitHub Pages)

Published at **https://axxx-institute.github.io/skills/** by
`.github/workflows/pages.yml` — a landing page
([`site/index.html`](site/index.html)) with a dedicated page per plugin:

- **`/mlspace-jobs.html`** ([`site/mlspace-jobs.html`](site/mlspace-jobs.html)) —
  the *experiments-as-code* pitch, the five launcher pillars and why each matters,
  the three skills, and the recommended workflow (quick-start → scaffold → reference).
- **`/paper-to-poster/`** — the four posterly examples re-rendered in AXXX style
  ([`…/examples/`](plugins/paper-to-poster/skills/paper-to-poster/examples/)).

## Repo docs

- `CONTEXT.md` — glossary of domain terms.
- `docs/adr/` — architecture decision records.
