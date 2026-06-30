# 1. paper-to-poster is AXXX-only (remove posterly's neutral / palette-derivation paths)

- Status: accepted
- Date: 2026-06-30
- Component: #2 paper-to-poster skill (AXXX restyle)

## Context

Upstream **posterly** ships venue- and lab-neutral. Its SKILL.md explicitly
argues *against* a single house style: a multi-step "palette derivation" routine
seeds colors from the affiliation brand / a logo / venue / figures, and the docs
warn "do **not** silently fall back to the one house style." The AXXX reference
poster (`compression_horizon/poster/poster.html`), by contrast, bakes the AXXX
brand into every surface (`:root` token block, Inter typeface, top accent bar,
arrow-glyph bullets, fixed affiliation logos).

We had to decide whether the ported skill keeps posterly's neutral default with
AXXX as an option, or commits to AXXX as the only output.

## Decision

The `paper-to-poster` skill is **AXXX-only**. It always emits the AXXX theme and
**removes** posterly's neutral-default and palette-derivation paths from the
ported SKILL body (the `:root` tokens are fixed to the AXXX palette, bullets are
the arrow glyph, the affiliation logo set is the AXXX set). There is no
house-style fallback and no "pick your colors" step.

## Consequences

- Simpler skill: the color-derivation logic, neutral templates' branding hooks,
  and the "echo the seed source" guidance are dropped or replaced with fixed AXXX
  tokens. One canonical look, fewer decisions per poster.
- Loss: the skill can no longer produce a differently-branded (non-AXXX) poster.
  That capability is intentionally out of scope (use upstream posterly for that).
- The posterly **gate tooling** (measure/polish/preflight/verify-final) is kept
  unchanged — only the *branding/default-selection* layer is AXXX-fixed.
- Hard-to-reverse: re-introducing neutral support later means re-porting the
  removed upstream paths.
