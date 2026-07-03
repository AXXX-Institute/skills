# AXXX-Institute / skills

AXXX-Institute's [Claude Code](https://claude.com/claude-code) **plugin** of
skills. Each skill lives under `skills/<name>/` with its own `SKILL.md`. The repo
is built to grow — `paper-to-poster` is the first skill and the worked example;
more AXXX skills can be added the same way.

## Skills

| Skill | What it does | License |
|---|---|---|
| [`paper-to-poster`](skills/paper-to-poster/) | Turn a paper into an **AXXX-branded** print-ready conference poster (single HTML/CSS → PDF), with affiliation logos pulled from this repo's asset releases. Ported from [posterly](https://github.com/Chenruishuo/posterly). | AGPL-3.0 (see below) |

## Using a skill

This repo is a Claude Code plugin (`.claude-plugin/plugin.json`). Two ways to consume it:

1. **As a plugin** — install the plugin so every `skills/<name>/SKILL.md` is available.
2. **Via a lockfile** — pin a single skill in another repo's `skills-lock.json`:

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
