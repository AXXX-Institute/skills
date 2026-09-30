# 13. The AIJ .pptx export embeds SB Sans Display (supersedes the by-name clause of 0012)

- Status: accepted
- Date: 2026-09-30
- Component: #paper-to-poster (AIJ format)
- Supersedes: the "fonts referenced by name, not embedded" clause of [0012](0012-aij-pptx-export-from-html.md); narrows [0011](0011-aij-fonts-from-cdn-frame-bundled.md)

## Context

A designer opened the exported AIJ `.pptx` and saw every text run in a substitute
face (Calibri-like) although the runs name SB Sans Display: PowerPoint only shows a
font that is installed or embedded. The organisers' own template avoids this by
embedding its fonts; our export (ADR 0012) referenced them by name only, and the
bundled template had its embedded fonts stripped (ADR 0011).

## Decision

- `aij/export_pptx.py` **embeds** the faces the poster's text uses by default
  (`aij/embed_fonts.py`; `--no-embed-fonts` opts out). They are downloaded **at
  export time** from the CDN URLs in `aij/fonts.css` — the files the HTML renders
  with — so no font file is committed to this repo's sources.
- They are named the way the organisers' desktop fonts are (one family per
  non-RIBBI weight, like the template's own "SB Sans Display Semibold"): "SB Sans
  Display" Regular + Bold, "SB Sans Display Light" and "SB Sans Display Semibold"
  as their own families — the typefaces every text run names (the title is
  Semibold 13 pt, as in the template). For every embedded face only the naming
  records (nameIDs 1/2/4/6; 16/17 dropped) and the style bits (OS/2 fsSelection,
  head.macStyle) are rewritten; outlines and metrics are untouched.
- Each face is an uncompressed **EOT 2.2** part `ppt/fonts/fontN.fntdata`, listed in
  `<p:embeddedFontLst>` with `embedTrueTypeFonts="1"` — the structure PowerPoint
  writes (its own parts are MTX-compressed EOT 2.2; the faces are installable,
  OS/2 fsType 0).
- The public gallery example's `.pptx` embeds the fonts too (maintainers' decision,
  2026-09-30), so the published showcase opens in SB Sans Display. This is the one
  place font data enters the public repo — inside that exported file, as in the
  organisers' own template; the skill's sources still carry none (ADR 0011).

## Consequences

- An exported poster can open in the real typeface on any machine; the file grows
  by ~100 KB per embedded face. A user's `.pptx` now contains the fonts, as the organisers' template does.
- Embedding needs network access at export time (like the rendering). If the fetch
  fails the export still completes, by-name only, with a loud `WARN`.
- Verified structurally only (schema-valid `presentation.xml`, EOT header
  round-trip, family names = run typefaces), not by opening PowerPoint.
