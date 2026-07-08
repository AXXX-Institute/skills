# Asset releases (`assets-vN`)

Affiliation logos and brand graphics for `paper-to-poster` are distributed as
**GitHub release assets**, not vendored per poster. The release is the
upstream-of-record; the skill fetches from a **pinned tag** and commits a copy
into each poster repo (`docs/adr/0002`).

## What's in a release

The payload is staged in the skill at
[`plugins/paper-to-poster/skills/paper-to-poster/axxx/assets/`](../plugins/paper-to-poster/skills/paper-to-poster/axxx/assets/)
and enumerated by its `MANIFEST.json`:

- Affiliation wordmarks: `airi_logo.svg`, `hse_logo.svg`, `innopolis_logo.svg`,
  `fusionbrain_combined.svg` (+ FusionBrain symbol/name variants).
- Brand bullet: `bullet_arrow.svg`.

(QR codes are per-poster and generated offline — never release assets.)

## Cutting `assets-v1` (one-time, when the repo exists on GitHub)

```bash
cd plugins/paper-to-poster/skills/paper-to-poster/axxx/assets
gh release create assets-v1 \
  --repo AXXX-Institute/skills \
  --title "AXXX poster assets v1" \
  --notes "Affiliation logos + brand bullet for paper-to-poster." \
  $(python -c "import json;print(' '.join(json.load(open('MANIFEST.json'))['files']))")
```

Verify a download URL resolves:
`https://github.com/AXXX-Institute/skills/releases/download/assets-v1/airi_logo.svg`

## Updating / bumping

- Non-breaking logo fix → re-upload the asset under the **same** `assets-v1` tag
  is discouraged (a pinned tag should be immutable). Prefer a new `assets-v2`.
- Breaking change (renamed/removed file) → cut `assets-v2`, update
  `plugins/paper-to-poster/skills/paper-to-poster/axxx/config.json` (`assets_tag`) and the staged
  `assets/` + `MANIFEST.json`.
- Posters already built keep their committed copy until re-fetched:
  `python axxx/fetch_assets.py --dest poster/images --tag assets-v2`.

Until the release exists, `fetch_assets.py` transparently falls back to the
bundled `axxx/assets/` copy, so the skill and the examples build offline.
