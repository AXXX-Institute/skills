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
| `fonts.css` | The single source of the SB Sans Display (Light 300 / Regular 400 / Semibold 600 / Bold 700) and SB Sans Text (Regular 400 / Semibold 600) CDN URLs. No font file is committed to this repo's sources. |
| `sync_fonts.py` | Copies `fonts.css` into a poster's `/* aij-fonts:begin … end */` block (`--check` reports drift). |
| `prepare_assets.py` | Copies the two frame graphics and required `airi_5_years_logo_white.svg` into a poster's `images/`. |
| `export_pptx.py` | Renders a finished AIJ poster and writes the editable `.pptx`: native text, native tables, pictures, and formulas as native Office equations with picture fallbacks, with SB Sans Display and Text embedded. Needs the `[pptx]` extra. |
| `embed_fonts.py` | Fetches the SB Sans Display and Text faces the text uses from the CDN at export time and embeds them in the `.pptx` (EOT parts + `<p:embeddedFontLst>`, the structure PowerPoint writes) — `docs/adr/0013`. |
| `white_logo.py` | Makes the white version of an affiliation logo (`<name>_white.png`, high-resolution; `--svg` for a vector) — the template shows logos in white, straight on the gradient, scaled by the primary graphic sign, excluding taglines (PNG output trims transparent outer margins). |

The frame assets are the organisers' — see `../NOTICE.md`.

## Typical flow (inside a poster repo)

```bash
cp <skill>/templates/portrait_aij.html poster/poster.html
python <skill>/aij/prepare_assets.py --dest poster/images
python <skill>/axxx/fetch_assets.py --dest poster/images --logos hse   # partner institutions only; AIRI copied above
python <skill>/aij/white_logo.py poster/images/hse_logo.svg   # white versions
# ... fill content, then the posterly gates:
python <skill>/tools/poster_check.py measure poster/poster.html
python <skill>/tools/poster_check.py polish  poster/poster.html
python <skill>/tools/render_preview.py poster/poster.html
pdffonts poster/poster_preview.pdf        # must list all used SBSansDisplay and SBSansText faces (MathJax faces are fine)
python <skill>/tools/poster_check.py verify-final poster/poster_preview.pdf --from-html poster/poster.html
# ... and the editable PowerPoint file (re-run after every HTML change):
pip install python-pptx mathml2omml lxml fonttools brotli
python <skill>/aij/export_pptx.py poster/poster.html     # -> poster/poster.pptx
```

## AIJ design contract

Use `№1`. Keep all paper content within the grey guide rectangle inside the white
panel: x=13.229167..177.270833 mm, y=39.599306..247.605903 mm. Preserve the
original PPTX guides. Shorten/rebalance content rather than reducing the type sizes.

| White-area role | Family | Size | Weight |
|---|---|---|---|
| Heading (`.section-title`) | SB Sans Display | 14 pt | Bold |
| Subheading (`.section-subtitle`) | SB Sans Display | 10 pt | Semibold |
| Block text and lists | SB Sans Text | 7 pt | Regular / Semibold |
| Captions and tables, including headers | SB Sans Text | 7 pt | Regular |

Main text and headings are black; meaningful keyword/result colour highlights
remain. Equations use the math renderer's font (Cambria Math in native Office
math) at the 7pt body scale. The frame keeps Display Semibold 13pt title/number,
Display Regular 7pt authors and Display Light 7pt footer.

AIRI's supplied five-year white logo is always first, followed by horizontal
partner institution logos. No AXXX or internal AIRI laboratory logos. Trim
transparent margins and preserve proportions. Scale and centre by **primary graphic
signs**, excluding taglines: AIRI's circle is 89/142 of the image height, set by
`data-mark-height="0.6267605634"` on its image. "5 лет" stays attached below.
For other assets, set `data-mark-height` and `data-mark-top` to the primary sign's
height and top as fractions of the source image height (defaults 1 and 0).
Use equal sign heights and equal gaps between complete logo images. The fitter
maximises sign height within the logo band while keeping all artwork in the footer.
Retain **text left → logos centre → QR right**: the primary signs' centres share
the text/QR centre axis; their heights need not equal the QR's height.
These rules affect AIJ only, not AXXX posters.

The `.pptx` embeds the used Display and Text families, including Semibold as
weight-specific families, downloaded from the CDN at export time. This is checked
structurally (names, EOT headers and geometry), not by opening PowerPoint here.
`--no-embed-fonts` references them by name only.

## If the CDN moves

Edit the URLs in `fonts.css`, then `python aij/sync_fonts.py templates/portrait_aij.html
examples/compression_horizon_aij/poster.html <every AIJ poster>`.
