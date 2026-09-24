# AXXX-Institute / skills

[![Docs — GitHub Pages](https://img.shields.io/badge/docs-axxx--institute.github.io%2Fskills-0689D4?logo=github&logoColor=white)](https://axxx-institute.github.io/skills/)

AXXX-Institute's provider-neutral plugin marketplace for
[Claude Code](https://claude.com/claude-code) and OpenAI Codex. Each plugin
lives under `plugins/<name>/` and ships one or more skills under
`plugins/<name>/skills/<skill>/`. The plugins are **installable independently**;
the repo is built to grow — more AXXX plugins can be added the same way.

## Plugins & skills

| Plugin | Skill | What it does | License |
|---|---|---|---|
| [`paper-to-poster`](plugins/paper-to-poster/) | [`paper-to-poster`](plugins/paper-to-poster/skills/paper-to-poster/) | Turn a paper into an **AXXX-branded** print-ready conference poster (single HTML/CSS → PDF), with affiliation logos pulled from this repo's asset releases. Ported from [posterly](https://github.com/Chenruishuo/posterly). | AGPL-3.0 (see below) |
| [`mlspace-jobs`](plugins/mlspace-jobs/) | [`mlspace-jobs-scaffold`](plugins/mlspace-jobs/skills/mlspace-jobs-scaffold/) | **Build** experiments-as-code MLSpace training + eval launchers (`run_train_jobs.py` / `run_eval.py` / `experiments.py`) into a repo — out-of-workdir artifacts, idempotent + in-progress-dedup submission, code staging; verified by a green `--dry` run. | MIT |
| [`mlspace-jobs`](plugins/mlspace-jobs/) | [`mlspace-jobs-quick-start`](plugins/mlspace-jobs/skills/mlspace-jobs-quick-start/) | **First-time** MLSpace setup: an interactive, one-step-at-a-time walkthrough from conda env → `mls` install → credentials → submitting and monitoring a first job. **Explicit-only** — launch it deliberately with `/mlspace-jobs-quick-start` (not auto-invoked, since it creates envs and installs packages). | MIT |
| [`mlspace-jobs`](plugins/mlspace-jobs/) | [`mlspace-jobs`](plugins/mlspace-jobs/skills/mlspace-jobs/) | **Operate** MLSpace once `mls` is configured: a command reference for monitoring, logs, waiting, killing jobs, `accelerate` multi-GPU config, and troubleshooting. | MIT |
| [`gitlab-ai`](plugins/gitlab-ai/) | [`setup-ci`](plugins/gitlab-ai/skills/setup-ci/) | Connect a repository to the shared GitLab review and agent-audit CI jobs while preserving its existing pipeline configuration. | MIT |
| [`gitlab-ai`](plugins/gitlab-ai/) | [`review-mr`](plugins/gitlab-ai/skills/review-mr/) | Review the current branch's GitLab MR with a fresh-context Claude or Codex worker, replace prior bot feedback, and post one summary plus CRITICAL inline discussions. | MIT |
| [`gitlab-ai`](plugins/gitlab-ai/) | [`repair-pipeline`](plugins/gitlab-ai/skills/repair-pipeline/) | Fetch the latest GitLab pipeline and failed-job logs, diagnose actionable failures, and repair the working tree. | MIT |
| [`gitlab-ai`](plugins/gitlab-ai/) | [`audit-agent-config`](plugins/gitlab-ai/skills/audit-agent-config/) | Verify repository-scoped Claude Code and Codex guidance against source, report stale claims and omissions, and optionally repair confirmed drift. | MIT |
| [`adversarial-review`](plugins/adversarial-review/) | [`adversarial-review`](plugins/adversarial-review/skills/adversarial-review/) | Review a committed implementation through an independent fresh-context agent, verifying every affected usage path before returning `APPROVE` or `REVISE`. **Explicit-only** — invoke `/adversarial-review` after non-trivial code changes. | MIT |

## Installation

This repo is a Claude Code **marketplace** (`.claude-plugin/marketplace.json`)
that hosts independently installable plugins. Install whichever you want. If you install
`paper-to-poster`, also install its **runtime dependencies** (last subsection).

### Method A — Plugin marketplace (recommended)

The same marketplace works from **Claude Code** and **OpenAI Codex**. Add it
once, then install only the plugins you need.

**Claude Code** — in a session:

```
/plugin marketplace add AXXX-Institute/skills
/plugin install paper-to-poster@axxx-institute   # the poster builder
/plugin install mlspace-jobs@axxx-institute       # the MLSpace job skills
/plugin install gitlab-ai@axxx-institute         # GitLab review, pipeline repair + agent config audit
/plugin install adversarial-review@axxx-institute # independent code review
```

**OpenAI Codex** — from your shell:

```bash
codex plugin marketplace add AXXX-Institute/skills
codex plugin add paper-to-poster@axxx-institute   # the poster builder
codex plugin add mlspace-jobs@axxx-institute       # the MLSpace job skills
codex plugin add gitlab-ai@axxx-institute         # GitLab review, pipeline repair + agent config audit
codex plugin add adversarial-review@axxx-institute # independent code review
```

Then connect the current repository to the shared GitLab CI gates:

```text
# Claude Code
/gitlab-ai:setup-ci

# OpenAI Codex
$gitlab-ai:setup-ci
```

The skill safely merges the ci-tools include into an existing `.gitlab-ci.yml`,
reuses or asks for the runner tag, validates the result, and explains which
masked GitLab token variable must be added. It never writes the token to the
repository.

### Method B — Ask an agent to install it (natural language)

Hand Claude Code the repo URL and say which plugin you want — it will add the
marketplace and install just that one:

> **https://github.com/AXXX-Institute/skills** — install the **mlspace-jobs** skills

> **https://github.com/AXXX-Institute/skills** — install the **paper-to-poster** skill

> **https://github.com/AXXX-Institute/skills** — install the **gitlab-ai** skills

> **https://github.com/AXXX-Institute/skills** — install the **adversarial-review** skill

Under the hood the agent runs `/plugin marketplace add AXXX-Institute/skills`
followed by `/plugin install <plugin>@axxx-institute` — nothing else is installed.

### Runtime dependencies

`paper-to-poster` renders posters with headless Chromium and processes images, so
its tools need Playwright + Chromium (and Pillow for figure/logo handling):

```bash
pip install playwright pillow
playwright install chromium
```

Without these, the skill's `tools/poster_check.py measure` and
`tools/render_preview.py` fail. The `mlspace-jobs` plugin has no such runtime
dependency (it drives the `mls` CLI, which the quick-start skill installs).

`gitlab-ai` requires `git` and `uv`; its Python scripts declare their own
dependencies through PEP 723. GitLab reads and writes require
`MR_AUTO_REVIEW_GITLAB_TOKEN` or `GITLAB_TOKEN`.

The GitLab host and project path are derived from the target repository's
`origin` remote. For example, an origin under `gitlab.example.com/group/repo`
uses `https://gitlab.example.com/api/v4`; no marketplace setting hard-codes a
GitLab server. In GitLab CI, the source branch is taken from the standard
`CI_MERGE_REQUEST_SOURCE_BRANCH_NAME`/`CI_COMMIT_*` variables when the checkout
is detached.

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
- **`gitlab-ai` plugin:** **MIT** — provider-neutral review, pipeline repair,
  and agent-guidance audit skills with deterministic GitLab helpers, covered by
  the repo-root MIT license.
- **`adversarial-review` plugin:** **MIT** — original work covered by the repo-root
  license and declared in both plugin manifests.
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
([`site/index.html`](site/index.html)) with plugin overview pages and one
generated `/<skill>/` page for every skill. Each skill page includes installation
and invocation commands, metadata, source links, and the complete `SKILL.md`.
All marketplace pages use the same visual system from `site/assets/styles.css`.

- **`/mlspace-jobs.html`** ([`site/mlspace-jobs.html`](site/mlspace-jobs.html)) —
  the *experiments-as-code* pitch: the three skills (in the order to use them) and
  the four properties the scaffold gives you, each as a with/without comparison.
- **`/paper-to-poster/`** — the skill page, linking to the preserved poster
  showcase at `/paper-to-poster/gallery.html` and its examples.
- **`/gitlab-ai.html`** ([`site/gitlab-ai.html`](site/gitlab-ai.html)) —
  the `setup-ci`, `review-mr`, `repair-pipeline`, and `audit-agent-config`
  workflows, shared model policy, and links to their individual skill pages.

## Repo docs

- `CONTEXT.md` — glossary of domain terms.
- `docs/adr/` — architecture decision records.
