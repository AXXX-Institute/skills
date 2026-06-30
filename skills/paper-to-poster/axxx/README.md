# AXXX layer

Everything that makes `paper-to-poster` **AXXX-only**. The upstream posterly body
(SKILL.md workflow, `tools/`, gates) is unchanged; this directory is the brand
layer bolted on top. See repo-root `docs/adr/0001` (AXXX-only), `0002` (logo
delivery), `0003` (AGPL licensing).

## Files

| File | Role |
|---|---|
| `config.json` | **Single source of truth** for the asset release: `owner`, `repo`, `assets_tag`, Pages URL. Retarget here. |
| `theme_tokens.css` | The AXXX `:root` palette (accent `#0689D4` …) + Inter as the only font. Ported from the AXXX reference poster. |
| `brand.css` | Brand graphics appended after the template `<style>`: top accent bar, arrow bullets (`images/bullet_arrow.svg`), affiliation-logo header strip. |
| `apply_theme.py` | Append the AXXX `<style id="axxx-theme">` + Inter `<link>` to a poster/template. **Idempotent.** Used to theme working posters and to generate the `templates/*_axxx.html`. |
| `logos.json` | Affiliation registry → release filename, Gate-E size class, chip. |
| `fetch_assets.py` | Download the chosen logos from the pinned `assets-vN` release → **commit into the poster's `images/`** (offline fallback to `assets/`). |
| `assets/` | Staged release payload = exactly what the `assets-v1` release contains (`MANIFEST.json` lists it). Also the offline fallback. |
| `deploy/github-pages.yml`, `deploy/gitlab-pages.yml` | Per-poster Pages deploy workflows offered after a successful build. |

## Typical flow (inside a poster repo)

```bash
cp <skill>/templates/landscape_4col_axxx.html poster/poster.html
python <skill>/axxx/fetch_assets.py --dest poster/images        # logos -> committed
python <skill>/axxx/apply_theme.py  poster/poster.html          # idempotent re-theme
# ... fill content, then posterly gates:
python <skill>/tools/poster_check.py measure poster/poster.html
python <skill>/tools/render_preview.py poster/poster.html
```

## Maintaining logos

The release is the upstream-of-record. To change a logo: update it in the
`assets-vN` GitHub release (and the staged `assets/` copy), bump the tag if the
change is breaking, and re-fetch in any poster that wants it. Posters already
built keep their committed copy until re-fetched (by design — `docs/adr/0002`).
