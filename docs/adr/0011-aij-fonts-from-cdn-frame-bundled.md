# 11. AIJ format: SB Sans Display is loaded from Sber's CDN (never vendored); the AIJ frame graphics are bundled in the skill

- Status: accepted
- Date: 2026-09-30
- Component: #paper-to-poster (AIJ format)

## Context

The [AIJ format](0010-two-fixed-poster-formats-axxx-and-aij.md) needs the
organisers' frame graphics (gradient background, AIJ header mark) and the **SB Sans
Display** family (Light / Regular / Bold). SB Sans is Sber's proprietary typeface;
`AXXX-Institute/skills` is a **public** repo, and anything published there (or in
the public gallery examples it hosts) cannot be un-published. ADR 0002's pattern for
logos is *fetch from a pinned release → commit into the poster repo* for offline
rendering.

## Decision

- **Fonts are never vendored — anywhere.** AIJ posters reference SB Sans Display via
  `@font-face` URLs on Sber's public design-system CDN
  (`cdn-app.sberdevices.ru/shared-static/…/SBSansDisplay.0.2.0/`), the same way the
  AXXX format already loads Inter from Google Fonts. No font file is committed to
  this repo, to its gallery examples, or to a user's poster repo.
- **The AIJ frame graphics are bundled** in the skill under `aij/assets/` and copied
  into the poster's `images/` at scaffold time — they *are* the format, and the
  template is distributed by the organisers to every participant.

## Considered options

- **Fetch fonts from the CDN and commit them into the poster repo** (ADR 0002 style)
  — initially chosen, then reversed: our own public gallery example would have
  committed SB Sans files into this repo.
- **Local-first `@font-face` with CDN fallback** — rejected as two delivery paths for
  one asset.
- **Fonts in the `assets-vN` release** — rejected: republishes a proprietary face.

## Consequences

- An AIJ poster needs network access to render in its real typeface; offline, it
  silently falls back. So "done" for an AIJ poster includes checking that the
  rendered PDF **embeds SB Sans Display** (e.g. `pdffonts`), not a fallback face.
- If the CDN path moves, every AIJ poster must be re-pointed; the URLs live in one
  place (`aij/fonts.css`, copied into posters by `aij/sync_fonts.py`).
- A rendered PDF (including the gallery example's) carries **subsets** of the faces
  it uses, as every PDF does — that is print output, not a font file. The `.pptx`
  export now embeds the faces it uses, fetched from the CDN at export time
  ([ADR 0013](0013-aij-pptx-embeds-sb-sans-display.md)); no font file is committed
  to this repo's sources — the gallery example's exported `.pptx` does carry them
  (maintainers' decision, ADR 0013).
