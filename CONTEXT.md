# Glossary (CONTEXT.md)

Canonical domain terms for the **axxx-skills** repo — a multi-skill Claude Code
plugin whose first skill is `paper-to-poster`. Glossary only — no implementation
detail. See `docs/adr/` for decisions and the skill sources for code.

## skills repo (AXXX-Institute/skills)
The public, org-owned Claude Code **plugin repository** that hosts one or more
skills under `skills/<name>/`. GitHub identity: **`AXXX-Institute/skills`**
(Pages at `axxx-institute.github.io/skills`, release assets at
`github.com/AXXX-Institute/skills/releases/...`); checked out locally as
`axxx-skills`. `paper-to-poster` is its first, example skill; the repo is built
so further skills can be added later.
_Avoid:_ "the poster repo" (that names the user's paper repo, not this one);
"axxx-skills" as the GitHub name (it's the local dir; the remote is
`AXXX-Institute/skills`).

## paper-to-poster
The skill ported from upstream **posterly** that turns a paper into a print-ready
conference poster, restyled so it **always** emits the AXXX brand look (no neutral
fallback). Keeps posterly's measure/polish gates and tooling.
_Avoid:_ "posterly" (that names the unmodified upstream skill we ported from).

## AXXX theme
The single, baked-in brand style the `paper-to-poster` skill always applies:
the AXXX `:root` token block (accent `#0689D4`, deep `#053957`, light-blue tints,
one semantic red), the **Inter** typeface, the top accent bar, arrow-glyph bullets,
and the affiliation logo set. There is no neutral/house-style fallback — the skill
is AXXX-only.
_Avoid:_ "neutral theme", "house style" (the upstream concepts we removed);
"palette derivation" (the upstream step we dropped).

## Affiliation logo
A brand mark for a contributing institution (AIRI, FusionBrain, HSE, Innopolis, …)
placed in the poster header. Maintained **centrally** as a versioned **GitHub
release asset** of `axxx-skills`; at build time the skill **fetches** the needed
logos from a pinned release tag and **commits the copy into the poster repo's
`images/`** so each poster is self-contained (offline render, Pages-deployable,
no remote `<img>`). Releases are the upstream-of-record; the poster vendors a
fetched copy. Upgrading = re-fetch a newer tag.
_Avoid:_ "venue logo" (that names the conference mark, a separate concept).

## Reference poster
`compression_horizon/poster/poster.html` — the hand-built, already-AXXX-styled
poster that is the canonical visual target for the AXXX theme.
_Avoid:_ "the template" (templates are the neutral posterly scaffolds).

## poster repo
The **user's own** project/paper repository in which the skill is invoked. The
skill writes the poster into `./poster/` here by default (mirroring
`compression_horizon/poster/`) and offers to add a Pages-deploy workflow.
_Avoid:_ "skills repo" (that is `AXXX-Institute/skills`, a different repo).

## assets release (assets-vN)
The versioned GitHub release of `AXXX-Institute/skills` that carries the
affiliation logo set (and bullet/QR marks). Tagged `assets-v1`, bumped on change;
the skill pins a tag and fetches from it. See [[affiliation-logo]].
_Avoid:_ "rolling tag" (a moving tag breaks the pinned-reproducibility contract).

## Pages gallery
The static GitHub Pages site of `AXXX-Institute/skills`
(`axxx-institute.github.io/skills`) that showcases the four posterly examples
re-rendered in AXXX style, listed by an `index.html`. Distinct from a single
poster repo's own Pages deploy.
_Avoid:_ "the demo" (the gallery is the published showcase, not a smoke test).
