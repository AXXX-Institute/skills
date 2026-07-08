# 3. paper-to-poster ships under AGPL-3.0 with preserved attribution; multi-skill repo uses per-skill license isolation

- Status: accepted
- Date: 2026-06-30
- Component: #1 skills-repo scaffold, #2 paper-to-poster skill

## Context

Upstream **posterly is licensed AGPL-3.0 © 2026 Ruishuo Chen** (`LICENSE`), and it
vendors a set of gate tools, three templates, and one component catalog from
**ARIS** that are **MIT-licensed**; `NOTICE.md` records that vendor boundary.
`paper-to-poster` is a **derivative work** of posterly, so AGPL-3.0's copyleft and
attribution terms attach to it. The `AXXX-Institute/skills` repo is **public** and
intended to hold **multiple, possibly differently-licensed** skills over time.

## Decision

- The `paper-to-poster` skill is distributed **under AGPL-3.0**. Its skill
  directory preserves posterly's **`LICENSE`** and **`NOTICE.md`** verbatim,
  retains the ARIS MIT attributions, and adds an attribution line crediting
  upstream posterly (Ruishuo Chen) and ARIS.
- The repo uses **per-skill license isolation**: the AGPL license lives **inside
  `skills/paper-to-poster/`**, not at the repo root, so future skills can carry
  their own licenses without being forced into AGPL by association. The repo root
  may carry a permissive or no-op top-level license plus a per-skill `LICENSE`
  pointer.
- AGPL source-availability is satisfied by the skill being public source in the
  repo.

## Consequences

- Legally clean port: copyleft honored, both attribution directions preserved.
- Per-skill isolation keeps the multi-skill repo flexible (a later MIT/Apache
  skill is unaffected by paper-to-poster's AGPL).
- Any future change that *combines* paper-to-poster code with another skill's
  code must respect AGPL — keep skill boundaries clean.
- **User confirmation flagged:** if AXXX-Institute requires a different licensing
  posture, that must be reconciled with AGPL before publishing (AGPL cannot be
  unilaterally relicensed away from posterly's terms).

## Update (2026-07-03)

The `AXXX-Institute/skills` repo was created on GitHub with a root **MIT**
`LICENSE`. That is adopted as the repo-scaffolding license (the "permissive
top-level license" anticipated above): MIT covers the plugin manifest, README,
gallery, and repo tooling, while `paper-to-poster` remains **AGPL-3.0** inside its
own directory. The two coexist because AGPL is confined to `skills/paper-to-poster/`
and is not relicensed by the MIT root.

## Update (2026-07-08)

The repo was restructured into a marketplace of per-directory plugins (ADR 0005).
The AGPL `paper-to-poster` skill — with its `LICENSE` and `NOTICE.md` — now lives
at **`plugins/paper-to-poster/skills/paper-to-poster/`**, and the MLSpace skills
are an independent MIT plugin at `plugins/mlspace-jobs/`. The per-skill isolation
described here is now enforced **structurally** by the plugin-directory boundary:
AGPL is confined to the `paper-to-poster` plugin directory, MIT to `mlspace-jobs`
and the root. Wherever this ADR says `skills/paper-to-poster/`, read
`plugins/paper-to-poster/skills/paper-to-poster/`.
