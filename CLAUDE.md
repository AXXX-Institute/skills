# CLAUDE.md — working in AXXX-Institute/skills

This repo is a Claude Code **marketplace** of independently-installable plugins,
**mirrored to OpenAI Codex** (Agent Skills standard). Root holds
`.claude-plugin/marketplace.json` (no root plugin manifest). Each plugin lives at
`plugins/<plugin>/` with its own `.claude-plugin/plugin.json` **and**
`.codex-plugin/plugin.json`, and ships skills at
`plugins/<plugin>/skills/<skill>/SKILL.md`. Codex discovery is via
`.agents/skills/<skill>` symlinks and `.agents/plugins/marketplace.json`.

Current plugins: `paper-to-poster` (AGPL-3.0), `mlspace-jobs` (MIT, three
skills), `gitlab-ai` (MIT, four provider-neutral skills), and
`adversarial-review` (MIT, one explicit-only skill). See `CONTEXT.md` for the
glossary and `docs/adr/` for decisions.

## Usage arms

- Marketplace validation → `.github/scripts/validate.py`; run `python3 .github/scripts/validate.py`.
- Plugin / skill validation → plugin-creator `validate_plugin.py` / skill-creator `quick_validate.py`.
- Claude installation → `/plugin marketplace add AXXX-Institute/skills`, `/plugin install <plugin>@axxx-institute`.
- Codex installation → `codex plugin marketplace add AXXX-Institute/skills`, `codex plugin add <plugin>@axxx-institute`.
- GitLab CI setup → `plugins/gitlab-ai/skills/setup-ci/`; invoke `/gitlab-ai:setup-ci`.
- GitLab review / repair / audit → `plugins/gitlab-ai/skills/{review-mr,repair-pipeline,audit-agent-config}/`.
- Headless Claude CI → `plugins/gitlab-ai/shared/ci/run_claude_gate.sh`; checks: `plugins/gitlab-ai/tests/`.
- Explicit adversarial review (Claude and Codex) → `plugins/adversarial-review/skills/adversarial-review/SKILL.md`.
- AXXX poster generation → `plugins/paper-to-poster/skills/paper-to-poster/axxx/`, `templates/*_axxx.html`.
- AIJ poster generation → `plugins/paper-to-poster/skills/paper-to-poster/aij/`, `templates/portrait_aij.html`.
- Poster editable export → `plugins/paper-to-poster/skills/paper-to-poster/aij/export_pptx.py`.
- Poster checks / rendering → `plugins/paper-to-poster/skills/paper-to-poster/tools/`; checks: that skill's `tests/`.
- Poster gallery → `plugins/paper-to-poster/skills/paper-to-poster/examples/`, including AIJ PDF/PPTX artifacts.
- GitHub Pages catalog → `.github/workflows/pages.yml`, `site/index.html`.
- Skill pages → `.github/scripts/build_skill_pages.py`, per-skill `README.md` and `SKILL.md`.
- Shared site presentation → `site/assets/styles.css`, `site/assets/site.js`.

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
2. **README files** — add the skill to the root **Plugins & skills** table and
   create `plugins/<plugin>/skills/<skill>/README.md` with Claude Code and Codex
   marketplace installation commands, invocation examples, and a `SKILL.md`
   link. CI enforces this contract.
3. **GitHub Pages** — describe the new skill on the site published by
   `.github/workflows/pages.yml`: MLSpace skills on
   [`site/mlspace-jobs.html`](site/mlspace-jobs.html), poster skills in the poster
   gallery (`plugins/paper-to-poster/skills/paper-to-poster/examples/index.html`),
   and a new plugin gets a card on the `site/index.html` landing plus its
   `/plugin install <name>@axxx-institute` line. Every skill also gets a generated
   `/<skill>/` page from `.github/scripts/build_skill_pages.py`; link it from the
   relevant landing page. The CI sync-guard enforces this.
4. **CONTEXT.md** — add/adjust the glossary term(s) for the new skill/plugin
   (glossary only — no implementation detail).
5. **docs/adr/** — if the addition involved a real, hard-to-reverse decision
   (topology, licensing, layout), record an ADR (`NNNN-slug.md`, next number).

## Conventions

- **Per-plugin license isolation.** A copyleft plugin (e.g. AGPL `paper-to-poster`)
  keeps its `LICENSE`/`NOTICE.md` inside its own plugin directory; original work
  is MIT under the repo root (declared in the plugin's `plugin.json`). Never let a
  copyleft plugin's license leak to the root or another plugin.
- **Invocation policy.** A skill whose ordinary execution immediately starts a
  long interactive takeover (e.g. `mlspace-jobs-quick-start`) sets
  `disable-model-invocation: true`. Skills that support useful read-only work but
  can also mutate external state remain discoverable and put an explicit user
  authorization gate immediately before the mutation.
- **Skills are the source of truth** for their own behavior; keep `SKILL.md`,
  its `references/`, and `evals/` internally consistent (e.g. if you renumber the
  scaffold's pillars, update every `pillar N` cross-reference and the eval notes).
- **Skill pages are generated.** Do not hand-edit `site/<skill>/index.html`.
  Update the skill's `README.md`, `SKILL.md`, or the shared generator instead.
- **Site styles are shared.** Do not add page-local `<style>` blocks to
  marketplace pages. Extend `site/assets/styles.css` with scoped selectors.
- **Commits:** conventional-commit prefixes (`feat:`, `fix:`, `refactor:`,
  `docs:`, `results:`); stage specific files (avoid `git add -A` when unrelated
  changes are present); commit only when the work is coherent and verified.
- **Validate before committing:** all `*.json` parse; no stale `skills/<name>/`
  paths remain after a move (grep); each plugin has its manifest and each skill a
  `SKILL.md`.
