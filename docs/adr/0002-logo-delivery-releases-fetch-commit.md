# 2. Affiliation logos: GitHub releases are upstream-of-record; skill fetches then commits into the poster repo

- Status: accepted
- Date: 2026-06-30
- Component: #3 affiliation-logo release pipeline

## Context

Affiliation logos (AIRI, FusionBrain, HSE, Innopolis, plus the arrow-bullet and
QR marks) must be **centrally maintainable** — the user asked for them as GitHub
release assets so they are "easily downloaded and maintained." But two existing
constraints pull the other way:

1. posterly's `measure` gate does a `networkidle` wait and the SKILL explicitly
   forbids **remote `<img>`** ("never leave a remote QR-service URL in the poster
   — it hangs `measure`'s networkidle wait and link-rots in print/archive").
2. Component #4 deploys posters to **GitHub Pages**, which serves dangling images
   unless the assets are present at deploy time; printed/archived posters must
   render offline and forever.

A "pure fetch at build, no vendor" stance (remote refs, or a gitignored cache)
was considered and rejected because it breaks (1) and (2).

## Decision

- The **logo set is published as a versioned GitHub release** of
  `AXXX-Institute/skills`, tagged `assets-vN` (`assets-v1`, bump on change). The
  release is the **upstream-of-record**.
- At build time the skill **fetches** the required logos from a **pinned tag**
  and **commits the copy into the poster repo's `images/`**. Posters reference
  **local relative paths** only — no remote `<img>`.
- Upgrading a poster's logos is an explicit **re-fetch of a newer tag**.

## Consequences

- Each poster repo is **self-contained**: offline render, print, Pages, and the
  `measure`/preflight gates all pass with no network at render time.
- Central maintenance is preserved: fix a logo once in the release, posters
  re-fetch on demand.
- Reproducibility: a pinned `assets-vN` tag is immutable-by-convention, so a
  re-fetch yields the same bytes; a rolling tag was rejected for this reason.
- Cost: logos are duplicated into every poster repo (acceptable — SVGs are tiny),
  and there is no automatic propagation of a logo fix to already-built posters
  (by design — re-fetch is explicit).
- Reverses an earlier in-interview "pure fetch, no vendor" answer once the gate /
  Pages conflict was surfaced.
