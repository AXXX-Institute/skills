# ADR 0009: Generate one documentation page per skill

## Status

Accepted.

## Context

Plugin-level landing pages explain bundles but do not give each skill a stable,
shareable documentation URL. Maintaining a second hand-written HTML copy of each
`SKILL.md` would allow the published instructions to drift from the installed
skill.

## Decision

- Every `plugins/<plugin>/skills/<skill>/` directory contains a `README.md` with
  Claude Code and Codex installation and invocation instructions.
- GitHub Pages generates `/<skill>/index.html` from marketplace metadata and the
  canonical `SKILL.md` during deployment.
- Plugin landing pages link to the generated routes.
- The existing poster example tree remains at `/paper-to-poster/`; its former
  gallery index is also published as `/paper-to-poster/gallery.html` before the
  generated skill page replaces the route index.

## Consequences

- Every skill has a predictable extensionless URL and GitHub-directory README.
- Published skill content cannot silently diverge from `SKILL.md`.
- Adding a skill requires a README, which repository validation enforces.
- The Pages build, rather than committed generated HTML, owns per-skill pages.
