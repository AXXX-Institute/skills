# CLAUDE.md — working in AXXX-Institute/skills

This repo is a Claude Code **marketplace** of independently-installable plugins,
**mirrored to OpenAI Codex** (Agent Skills standard). Root holds
`.claude-plugin/marketplace.json` (no root plugin manifest). Each plugin lives at
`plugins/<plugin>/` with its own `.claude-plugin/plugin.json` **and**
`.codex-plugin/plugin.json`, and ships skills at
`plugins/<plugin>/skills/<skill>/SKILL.md`. Codex discovery is via
`.agents/skills/<skill>` symlinks and `.agents/plugins/marketplace.json`.

Current plugins: `paper-to-poster` (AGPL-3.0) and `mlspace-jobs` (MIT, three
skills). See `CONTEXT.md` for the glossary and `docs/adr/` for decisions.

## When adding, renaming, or removing a skill or plugin — update ALL of these

This is a hard requirement. A new skill is not "done" until every item is updated
in the **same change**; don't stop at dropping a `SKILL.md`.

1. **Manifests — Claude *and* Codex (CI enforces parity).**
   - New plugin → add `plugins/<name>/` with **both** `.claude-plugin/plugin.json`
     and `.codex-plugin/plugin.json` (same `name`; Codex uses `"skills": "./skills/"`).
     Add an entry to **both** catalogs: `.claude-plugin/marketplace.json`
     (`source: "./plugins/<name>"`) and `.agents/plugins/marketplace.json`
     (`source: {source: "local", path: "./plugins/<name>"}`).
   - New skill inside an existing plugin → add `plugins/<plugin>/skills/<skill>/`
     (auto-discovered), **and** a `.agents/skills/<skill>` symlink →
     `../../plugins/<plugin>/skills/<skill>` so Codex sees it. Refresh the plugin's
     `plugin.json` description if scope changed.
   - Explicit-only skill → `disable-model-invocation: true` (Claude) **and** an
     `agents/openai.yaml` with `allow_implicit_invocation: false` (Codex) beside
     its `SKILL.md`.
2. **README.md** — add the skill to the **Plugins & skills** table (with its new
   `plugins/<plugin>/skills/<skill>/` path and license), and update the install
   instructions if a new plugin was introduced.
3. **GitHub Pages** — describe the new skill on the site published by
   `.github/workflows/pages.yml`: MLSpace skills on
   [`site/mlspace-jobs.html`](site/mlspace-jobs.html), poster skills in the poster
   gallery (`plugins/paper-to-poster/skills/paper-to-poster/examples/index.html`),
   and a new plugin gets a card on the `site/index.html` landing plus its
   `/plugin install <name>@axxx-institute` line. Every skill must be described on
   the site — the CI sync-guard enforces this. **Keep the Pages skill list in sync
   with the actual skills.**
4. **CONTEXT.md** — add/adjust the glossary term(s) for the new skill/plugin
   (glossary only — no implementation detail).
5. **docs/adr/** — if the addition involved a real, hard-to-reverse decision
   (topology, licensing, layout), record an ADR (`NNNN-slug.md`, next number).

## Conventions

- **Per-plugin license isolation.** A copyleft plugin (e.g. AGPL `paper-to-poster`)
  keeps its `LICENSE`/`NOTICE.md` inside its own plugin directory; original work
  is MIT under the repo root (declared in the plugin's `plugin.json`). Never let a
  copyleft plugin's license leak to the root or another plugin.
- **Invocation policy.** A skill with side effects or a long interactive takeover
  (e.g. `mlspace-jobs-quick-start`, which creates conda envs, installs packages,
  and writes credentials) sets `disable-model-invocation: true` so it runs only
  when the user types `/<skill>`. Skills meant to activate from natural language
  (e.g. `mlspace-jobs-scaffold`, `mlspace-jobs`) leave it unset.
- **Skills are the source of truth** for their own behavior; keep `SKILL.md`,
  its `references/`, and `evals/` internally consistent (e.g. if you renumber the
  scaffold's pillars, update every `pillar N` cross-reference and the eval notes).
- **Commits:** conventional-commit prefixes (`feat:`, `fix:`, `refactor:`,
  `docs:`, `results:`); stage specific files (avoid `git add -A` when unrelated
  changes are present); commit only when the work is coherent and verified.
- **Validate before committing:** all `*.json` parse; no stale `skills/<name>/`
  paths remain after a move (grep); each plugin has its manifest and each skill a
  `SKILL.md`.
