# AIJ layer

Everything the **AIJ poster format** adds to `paper-to-poster`: the AI Journey
organisers' poster template reproduced as one HTML scaffold
(`templates/portrait_aij.html`), rendered to PDF by the usual posterly pipeline,
and exported to an editable `.pptx` in the organisers' own template. The AXXX
format lives next door in `axxx/`. See repo-root `docs/adr/0010` (two fixed
formats), `0011` (fonts from the CDN, frame bundled), `0012` (PPTX export).

## Files

| File | Role |
|---|---|
| `assets/aij_template.pptx` | The organisers' template (190.5×275.2 mm slide) with its **embedded fonts stripped** and its sample/instruction artwork (arrows, the "COMPANY" sample-logo sheet, the sample QR, the package thumbnail) **blanked** — the slide XML, master, background and AIJ mark are byte-identical to the organisers' file. The base of the PPTX export and the geometry reference the tests compare against. |
| `assets/aij_background.png` | Frame background: the gradient around the white panel (the panel itself is transparent; the slide is white). |
| `assets/aij_mark.svg` | The AIJ header mark ("Путешествие в мир искусственного интеллекта"). |
| `fonts.css` | The single source of the SB Sans Display (Light 300 / Regular 400 / Semibold 600 / Bold 700) CDN URLs. No font file is committed to this repo's sources. |
| `sync_fonts.py` | Copies `fonts.css` into a poster's `/* aij-fonts:begin … end */` block (`--check` reports drift). |
| `prepare_assets.py` | Copies the two frame graphics into a poster's `images/`. |
| `export_pptx.py` | Renders a finished AIJ poster and writes the editable `.pptx`: native text, native tables, pictures, and formulas as native Office equations with picture fallbacks, with SB Sans Display embedded. Needs the `[pptx]` extra. |
| `embed_fonts.py` | Fetches the SB Sans Display faces the text uses (Light/Regular/Semibold/Bold) from the CDN at export time and embeds them in the `.pptx` (EOT parts + `<p:embeddedFontLst>`, the structure PowerPoint writes) — `docs/adr/0013`. |
| `white_logo.py` | Makes the white version of an affiliation logo (`<name>_white.svg`/`.png`) — the template shows logos in white, straight on the gradient. |

The frame assets are the organisers' — see `../NOTICE.md`.

## Typical flow (inside a poster repo)

```bash
cp <skill>/templates/portrait_aij.html poster/poster.html
python <skill>/aij/prepare_assets.py --dest poster/images
python <skill>/axxx/fetch_assets.py --dest poster/images --logos airi hse   # ONLY this paper's logos
python <skill>/aij/white_logo.py poster/images/airi_logo.svg poster/images/hse_logo.svg   # white versions
# ... fill content, then the posterly gates:
python <skill>/tools/poster_check.py measure poster/poster.html
python <skill>/tools/poster_check.py polish  poster/poster.html
python <skill>/tools/render_preview.py poster/poster.html
pdffonts poster/poster_preview.pdf        # must list SBSansDisplay-Light/-Regular/-Semibold (+ -Bold with <strong>; DejaVu from MathJax is fine)
python <skill>/tools/poster_check.py verify-final poster/poster_preview.pdf --from-html poster/poster.html
# ... and the editable PowerPoint file (re-run after every HTML change):
pip install python-pptx mathml2omml lxml fonttools brotli
python <skill>/aij/export_pptx.py poster/poster.html     # -> poster/poster.pptx
```

## Type roles

| Role | Face | Size | Used for |
|---|---|---|---|
| Title | SB Sans Display Semibold | 13 pt | poster title, poster number (as the template) |
| Subtitle | SB Sans Display (Regular) | 7 pt | author line, section headings, table heads |
| Body | SB Sans Display Light | 7 pt | text, lists, captions, table cells, footer |

In the `.pptx` the text uses `SB Sans Display` (Regular / Bold), `SB Sans Display
Light` and `SB Sans Display Semibold`, and those faces are **embedded** in the file
(fetched from the CDN at export time), so PowerPoint can show the real typeface
without SB Sans installed (the structure PowerPoint writes; checked structurally — schema, font names, EOT headers — not yet by opening the file in PowerPoint). `--no-embed-fonts` references them
by name only.

## If the CDN moves

Edit the URLs in `fonts.css`, then `python aij/sync_fonts.py templates/portrait_aij.html
examples/compression_horizon_aij/poster.html <every AIJ poster>`.
