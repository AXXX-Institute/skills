# 10. paper-to-poster ships two fixed poster formats — AXXX and AIJ (supersedes 0001)

- Status: accepted
- Date: 2026-09-30
- Component: #paper-to-poster
- Supersedes: [0001](0001-axxx-only-theme.md)

## Context

ADR 0001 made `paper-to-poster` **AXXX-only**: one baked-in brand, no neutral
fallback, no palette derivation. AXXX papers are now also presented at **AI Journey
(AIJ)**, whose organisers require their own poster template (a fixed 190.5×275.2 mm
portrait sheet with a gradient frame, AIJ header mark, header/footer slots, and SB
Sans Display typography). A poster built in the AXXX look cannot be submitted there.

## Decision

`paper-to-poster` ships exactly **two fixed poster formats**, **AXXX** (the existing
look, renamed from "the AXXX theme" in prose only — its code under `axxx/` and
`templates/*_axxx.html` is unchanged) and **AIJ** (new, under `aij/` +
`templates/portrait_aij.html`). The format is the **first** design-discovery
question (suggested from the venue: AI Journey → AIJ, otherwise AXXX; always
confirmed). There is still **no** neutral/house-style fallback and no palette
derivation — each format is fixed.

## Considered options

- **Separate `paper-to-poster-aij` skill, keep 0001 intact** — rejected: duplicates
  the whole posterly workflow and gate tooling for one frame, and the two skills
  would drift.
- **AXXX by default, AIJ only on explicit request** — rejected: silently producing
  the wrong format for an AIJ submission is the costly failure; asking once is cheap.

## Consequences

- "AXXX-only" wording is retired from SKILL.md, README, Pages, both `plugin.json`
  manifests, and CONTEXT.md; they describe two formats.
- The format is asked first, on its own (SKILL.md Step 0). AIJ fixes canvas and
  layout, so for AIJ the venue-guideline lookup (Step 0.1) and the layout choice
  are skipped.
- Adding a third format later means another sibling layer + template, not a
  neutral mode.
