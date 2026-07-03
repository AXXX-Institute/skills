# AXXX-Institute / skills

AXXX-Institute's [Claude Code](https://claude.com/claude-code) **plugin** of
skills. Each skill lives under `skills/<name>/` with its own `SKILL.md`. The repo
is built to grow — `paper-to-poster` is the first skill and the worked example;
more AXXX skills can be added the same way.

## Skills

| Skill | What it does | License |
|---|---|---|
| [`paper-to-poster`](skills/paper-to-poster/) | Turn a paper into an **AXXX-branded** print-ready conference poster (single HTML/CSS → PDF), with affiliation logos pulled from this repo's asset releases. Ported from [posterly](https://github.com/Chenruishuo/posterly). | AGPL-3.0 (see below) |

## Installation

This repo is both a Claude Code **plugin** (`.claude-plugin/plugin.json`) and a
**marketplace** (`.claude-plugin/marketplace.json`). Pick one method. After any
method, install the **runtime dependencies** (last subsection) — the poster tools
need them.

### Method A — Claude Code plugin marketplace (recommended)

In a Claude Code session, add this repo as a marketplace and install the plugin:

```
/plugin marketplace add AXXX-Institute/skills
/plugin install axxx-skills@axxx-institute
```

- `axxx-skills` is the plugin; `axxx-institute` is the marketplace name (from
  `marketplace.json`).
- Installing the plugin exposes **every** skill under `skills/` (currently
  `paper-to-poster`).
- Update later with `/plugin marketplace update axxx-institute`; remove with
  `/plugin uninstall axxx-skills@axxx-institute`.
- List/enable from the picker with `/plugin`.

### Method B — Manual copy (works in any setup, no marketplace)

A skill is just a directory containing `SKILL.md`. Clone the repo and drop the
skill into a Claude Code skills directory:

```bash
git clone https://github.com/AXXX-Institute/skills.git axxx-skills

# Project-local (available in one project): from your project root
mkdir -p .claude/skills
cp -r axxx-skills/skills/paper-to-poster .claude/skills/paper-to-poster
#   …or symlink to track updates:
# ln -s "$(pwd)/../axxx-skills/skills/paper-to-poster" .claude/skills/paper-to-poster

# Global (available in every project)
mkdir -p ~/.claude/skills
cp -r axxx-skills/skills/paper-to-poster ~/.claude/skills/paper-to-poster
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
      "skillPath": "skills/paper-to-poster/SKILL.md"
    }
  }
}
```

See [`skills-lock.example.json`](skills-lock.example.json).

### Runtime dependencies (required for all methods)

`paper-to-poster` renders posters with headless Chromium and processes images, so
its tools need Playwright + Chromium (and Pillow for figure/logo handling):

```bash
pip install playwright pillow
playwright install chromium
```

Without these, `tools/poster_check.py measure` and `tools/render_preview.py` fail.

### Using it

Once installed, just ask Claude in a session — e.g. *"make an AXXX poster for this
paper"* or *"turn paper.tex into an ICML poster"*. The skill activates from its
description and walks the workflow in `skills/paper-to-poster/SKILL.md`. The poster
is written to `./poster/` in your current repo, and Claude offers a GitHub/GitLab
Pages deploy workflow.

## Licensing

This repo uses **per-skill license isolation**:

- **Repo scaffolding & docs (root):** **MIT** (`LICENSE`) — the plugin manifest,
  README, gallery, and repo tooling.
- **`paper-to-poster` skill:** **AGPL-3.0** (`skills/paper-to-poster/LICENSE`,
  attribution in `skills/paper-to-poster/NOTICE.md`) because it derives from
  [posterly](https://github.com/Chenruishuo/posterly). AGPL applies to that skill
  directory; it is **not** relicensed by the MIT root.
- **Future skills** carry their own `LICENSE` under `skills/<name>/`.

The permissive MIT root and the copyleft AGPL skill coexist precisely because the
AGPL is confined to its own directory. See [`docs/adr/0003`](docs/adr/0003-agpl-license-isolation.md).

## Asset releases

Affiliation logos and brand graphics are published as versioned **GitHub release
assets** (tag `assets-v1`). The `paper-to-poster` skill fetches the logos it needs
from a pinned tag and commits a copy into each poster repo, so posters render
offline and on Pages with no remote images. See
[`docs/RELEASE-assets.md`](docs/RELEASE-assets.md) and
[`docs/adr/0002`](docs/adr/0002-logo-delivery-releases-fetch-commit.md).

## Examples gallery

The four posterly examples, re-rendered in AXXX style, are published to GitHub
Pages: **https://axxx-institute.github.io/skills** (built by `examples/` — see
[`examples/README.md`](examples/README.md)).

## Repo docs

- `CONTEXT.md` — glossary of domain terms.
- `docs/adr/` — architecture decision records.
