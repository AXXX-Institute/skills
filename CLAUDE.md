# CLAUDE.md — working in AXXX-Institute/skills

This repo is a Claude Code **marketplace** of independently-installable plugins.
Root holds `.claude-plugin/marketplace.json` (no root plugin manifest). Each
plugin lives at `plugins/<plugin>/` with its own `.claude-plugin/plugin.json` and
ships skills at `plugins/<plugin>/skills/<skill>/SKILL.md`.

Current plugins: `paper-to-poster` (AGPL-3.0) and `mlspace-jobs` (MIT, three
skills). See `CONTEXT.md` for the glossary and `docs/adr/` for decisions.

## When adding, renaming, or removing a skill or plugin — update ALL of these

This is a hard requirement. A new skill is not "done" until every item is updated
in the **same change**; don't stop at dropping a `SKILL.md`.

1. **Manifests**
   - New plugin → add a directory `plugins/<name>/` with `.claude-plugin/plugin.json`,
     and add an entry to `.claude-plugin/marketplace.json` (relative `source:
     "./plugins/<name>"`, plus `description`/`tags`/`license`).
   - New skill inside an existing plugin → just add `plugins/<plugin>/skills/<skill>/`
     (auto-discovered); refresh the plugin's `plugin.json` description if its scope
     changed.
2. **README.md** — add the skill to the **Plugins & skills** table (with its new
   `plugins/<plugin>/skills/<skill>/` path and license), and update the install
   instructions if a new plugin was introduced.
3. **GitHub Pages** — add the skill's description to the **Plugins & skills**
   section of
   `plugins/paper-to-poster/skills/paper-to-poster/examples/index.html` (the Pages
   site root, published by `.github/workflows/pages.yml`). Every skill on the repo
   must have a card/row there with a one-line description and, for a new plugin,
   its `/plugin install <name>@axxx-institute` line. **Always keep the Pages
   skill list in sync with the actual skills in the repo.**
4. **CONTEXT.md** — add/adjust the glossary term(s) for the new skill/plugin
   (glossary only — no implementation detail).
5. **docs/adr/** — if the addition involved a real, hard-to-reverse decision
   (topology, licensing, layout), record an ADR (`NNNN-slug.md`, next number).

## Conventions

- **Per-plugin license isolation.** A copyleft plugin (e.g. AGPL `paper-to-poster`)
  keeps its `LICENSE`/`NOTICE.md` inside its own plugin directory; original work
  is MIT under the repo root (declared in the plugin's `plugin.json`). Never let a
  copyleft plugin's license leak to the root or another plugin.
- **Skills are the source of truth** for their own behavior; keep `SKILL.md`,
  its `references/`, and `evals/` internally consistent (e.g. if you renumber the
  scaffold's pillars, update every `pillar N` cross-reference and the eval notes).
- **Commits:** conventional-commit prefixes (`feat:`, `fix:`, `refactor:`,
  `docs:`, `results:`); stage specific files (avoid `git add -A` when unrelated
  changes are present); commit only when the work is coherent and verified.
- **Validate before committing:** all `*.json` parse; no stale `skills/<name>/`
  paths remain after a move (grep); each plugin has its manifest and each skill a
  `SKILL.md`.
