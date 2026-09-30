# 12. AIJ posters are exported to an editable .pptx from the finished HTML (HTML stays the source of truth)

- Status: accepted
- Date: 2026-09-30
- Component: #paper-to-poster (AIJ format)

## Context

AI Journey organisers accept posters in **their own `.pptx` template**, and authors
need to make last-minute text edits in PowerPoint. The skill's whole quality
pipeline (measure / polish / preflight / verify-final gates) runs on a single HTML
file rendered by Chromium. We had to decide what the `.pptx` *is*.

## Decision

- For the AIJ format the skill **always** produces a `.pptx` next to the PDF
  (never for AXXX). The HTML poster remains the **only source of truth**; the
  `.pptx` is a one-way **export** built after the gates pass.
- The exporter opens a copy of the **organisers' template** bundled in the skill,
  **with its embedded fonts stripped** (per [ADR 0011](0011-aij-fonts-from-cdn-frame-bundled.md)
  no SB Sans file ships in this repo); master, background and AIJ mark are kept.
  Fonts are referenced **by name** (SB Sans Display / SB Sans Display Light) — the
  machine opening the file must have them installed.
- Content is re-expressed natively at the Chromium-rendered geometry: text as
  editable text frames, tables as native PowerPoint tables, figures as pictures,
  and **math as native Office equations** (MathJax's MathML → OMML via
  `mathml2omml`), each wrapped in `mc:AlternateContent` with a rendered-PNG fallback
  for non-Office viewers. An equation that fails to convert degrades to a picture
  and is reported — never dropped silently.

## Considered options

- **Build AIJ natively in pptx** (python-pptx as the layout engine) — rejected: it
  forfeits every existing gate and needs a second layout engine.
- **Content area as one picture** — rejected: the text would not be editable.
- **Inline math as Unicode text** — chosen first, then replaced by native equations
  so formulas stay editable as formulas.
- **pandoc for TeX → OMML** — rejected: a system dependency on the user's machine,
  and a second TeX parse that can diverge from what MathJax rendered.

## Consequences

- PowerPoint line-breaking differs from Chromium, so text frames can reflow; the
  PDF is the visual reference, and the `.pptx` is verified by **automated
  structural/geometry tests only** (python-pptx re-read, OMML validated against the
  ECMA-376 schema), not by a PowerPoint render.
- `python-pptx` and `mathml2omml` become an optional `[pptx]` extra of the skill.
