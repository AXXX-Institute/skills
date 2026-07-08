# 5. Split the repo into a marketplace of independently-installable plugins

- Status: accepted
- Date: 2026-07-08
- Component: #skills-repo scaffold, #paper-to-poster, #mlspace-jobs

## Context

The repo began as a single Claude Code plugin (`axxx-skills`, `source: "./"`) that
exposed **every** skill under `skills/`. After the MLSpace job skills landed
(ADR 0004), that meant installing the plugin pulled in both `paper-to-poster` and
the three `mlspace-jobs*` skills together. We want the MLSpace skills to be
installable **on their own**, without the poster (and vice-versa).

A plugin's `skills` manifest field only **adds to** the default `skills/` scan —
it cannot narrow what a plugin exposes (Claude Code plugins reference). So a single
root plugin can't be scoped to a subset of `skills/`. Independent installation
requires **separate plugins**, and a plugin is installed by copying its own
directory (it can't reference files outside it). Therefore each plugin needs its
own directory with its own `.claude-plugin/plugin.json` and `skills/`.

## Decision

Restructure the repo into a **marketplace of two plugins**, each in its own
directory:

```
.claude-plugin/marketplace.json      # lists both plugins (relative ./plugins/* sources)
plugins/
  paper-to-poster/
    .claude-plugin/plugin.json        # name: paper-to-poster, AGPL-3.0
    skills/paper-to-poster/           # + its LICENSE / NOTICE.md
  mlspace-jobs/
    .claude-plugin/plugin.json        # name: mlspace-jobs, MIT
    skills/{mlspace-jobs,mlspace-jobs-quick-start,mlspace-jobs-scaffold}/
```

- The repo root is now a **pure marketplace** — the root `.claude-plugin/plugin.json`
  is removed; only `marketplace.json` remains at the root.
- `marketplace.json` lists two plugins with relative sources
  `./plugins/paper-to-poster` and `./plugins/mlspace-jobs`.
- Users install independently:
  `/plugin install paper-to-poster@axxx-institute` and/or
  `/plugin install mlspace-jobs@axxx-institute`.
- The `mlspace-jobs` plugin bundles all three MLSpace skills (they share the
  "MLSpace jobs" domain and are installed as a set); `paper-to-poster` bundles the
  one poster skill.
- All references to the old `skills/<name>/` paths were updated: `README.md`,
  `.github/workflows/pages.yml`, `docs/RELEASE-assets.md`, `skills-lock.example.json`,
  and the examples gallery `index.html`.

## Consequences

- The poster and the MLSpace tooling install and update independently; a user who
  only wants MLSpace job launchers no longer pulls in the AGPL poster (and its
  Playwright/Chromium runtime deps).
- Per-plugin license isolation is now **structural**: AGPL lives entirely inside
  `plugins/paper-to-poster/`, MIT inside `plugins/mlspace-jobs/`, MIT at the root.
  This strengthens ADR 0003 (the AGPL path moved — see its update note).
- The published install command changed from `axxx-skills@axxx-institute` to two
  plugin-specific commands. The old plugin name `axxx-skills` is retired; anyone
  who installed it should reinstall the plugin(s) they want.
- Adding a future plugin = a new `plugins/<name>/` directory + one entry in
  `marketplace.json`; no impact on existing plugins.
