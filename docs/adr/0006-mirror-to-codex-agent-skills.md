# 6. Mirror the marketplace to OpenAI Codex via the Agent Skills standard

- Status: accepted
- Date: 2026-07-08
- Component: #skills-repo scaffold, #paper-to-poster, #mlspace-jobs

## Context

The skills are authored to the cross-tool **Agent Skills** open standard
(`SKILL.md` with `name`/`description` frontmatter). OpenAI **Codex** supports the
same standard, plus a parallel plugin + marketplace system very close to Claude
Code's: `.codex-plugin/plugin.json` ≈ `.claude-plugin/plugin.json`, both with
`skills/<name>/SKILL.md`. We want the *identical* plugins and skills usable from
Codex **without a second copy** of any `SKILL.md`.

Confirmed from OpenAI Codex docs (`developers.openai.com/codex/*`): Codex scans
`$REPO_ROOT/.agents/skills` for skills; a plugin marketplace lives at
`.agents/plugins/marketplace.json`; and Codex ignores Claude-only frontmatter
(`disable-model-invocation`), using an optional `agents/openai.yaml`
(`allow_implicit_invocation`) for invocation control.

## Decision

- Each plugin directory carries **both** `.claude-plugin/plugin.json` and
  `.codex-plugin/plugin.json` (same `name`; the Codex manifest sets
  `"skills": "./skills/"`), sharing the single `skills/` tree.
- A Codex marketplace at `.agents/plugins/marketplace.json` lists the same two
  plugins with `local` sources.
- Codex repo-local discovery is wired via **`.agents/skills/<skill>` symlinks** to
  the canonical `plugins/<plugin>/skills/<skill>` dirs — exactly one copy of every
  `SKILL.md`.
- The explicit-only `mlspace-jobs-quick-start` reproduces its Claude Code
  `disable-model-invocation: true` for Codex via
  `agents/openai.yaml` (`allow_implicit_invocation: false`) beside its `SKILL.md`.
- CI (`.github/scripts/validate.py`) asserts the Codex and Claude Code plugin
  lists, per-plugin manifests, and skill sets stay identical.

## Consequences

- One source of truth per skill; both tools stay in lockstep, enforced by CI —
  drift (a missing symlink, manifest, or marketplace entry) fails the build.
- Adding a plugin or skill now also requires the Codex mirror (documented in
  `CLAUDE.md`).
- **Symlink caveat:** non-symlink-friendly checkouts (e.g. Windows) may need
  CI-synced real copies instead; acceptable for this repo, which targets Linux.
- The Codex `marketplace.json` schema (`source`/`policy`/`category`) is taken from
  current OpenAI Codex docs; revisit if it changes.
