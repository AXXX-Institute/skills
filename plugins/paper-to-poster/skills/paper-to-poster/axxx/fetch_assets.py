#!/usr/bin/env python3
"""Fetch AXXX affiliation logos from the pinned `assets-vN` GitHub release and
COMMIT them into a poster repo's images/ directory.

Design (see docs/adr/0002): the GitHub release is the upstream-of-record; each
poster vendors a *fetched copy* so it renders offline / on Pages / under
posterly's `measure` gate with no remote <img>. Upgrading = re-fetch a newer tag.

Offline / unreachable release -> falls back to the bundled staging copy in
`axxx/assets/` so the skill (and its examples) build with no network. Either way
the bytes land locally in images/; nothing remote is left in the poster.

Usage:
  python axxx/fetch_assets.py --dest poster/images            # bullet glyph only
  python axxx/fetch_assets.py --dest poster/images --logos airi hse   # only this paper's affiliations
  python axxx/fetch_assets.py --dest poster/images --all      # every asset (release staging only)
  python axxx/fetch_assets.py --dest poster/images --tag assets-v2
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config.json").read_text())
LOGOS = json.loads((HERE / "logos.json").read_text())
STAGE = HERE / "assets"  # bundled offline fallback == release payload


def _release_base(tag: str) -> str:
    return f"https://github.com/{CONFIG['owner']}/{CONFIG['repo']}/releases/download/{tag}"


def _files_for(keys: list[str], include_all: bool) -> list[str]:
    if include_all:
        return list(json.loads((STAGE / "MANIFEST.json").read_text())["files"])
    files: list[str] = []
    for key in keys:
        if key in LOGOS["logos"]:
            files.append(LOGOS["logos"][key]["file"])
        elif key in LOGOS:  # e.g. bullet_arrow
            files.append(LOGOS[key]["file"])
        else:
            print(f"  ! unknown logo key '{key}' (see logos.json)", file=sys.stderr)
    # bullet_arrow is always needed by brand.css
    files.append(LOGOS["bullet_arrow"]["file"])
    # dedupe, preserve order
    seen: set[str] = set()
    return [f for f in files if not (f in seen or seen.add(f))]


def _fetch_one(fname: str, dest_dir: Path, tag: str) -> str:
    """Return 'release' | 'fallback' depending on where the bytes came from."""
    out = dest_dir / fname
    url = f"{_release_base(tag)}/{fname}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            out.write_bytes(resp.read())
        return "release"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        src = STAGE / fname
        if not src.exists():
            raise SystemExit(f"  x {fname}: release unreachable AND no bundled fallback")
        shutil.copyfile(src, out)
        return "fallback"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", required=True, help="poster images/ dir to populate (created if missing)")
    ap.add_argument("--logos", nargs="*", default=[],
                    help="affiliation keys to fetch — pass ONLY the institutions that "
                         "actually authored this paper (e.g. `airi hse`). Default: none "
                         "(fetch just the brand bullet). Never dump the whole consortium.")
    ap.add_argument("--all", action="store_true", help="fetch every asset in the release")
    ap.add_argument("--tag", default=CONFIG["assets_tag"], help="release tag to pin (default: %(default)s)")
    args = ap.parse_args()

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    files = _files_for(args.logos, args.all)

    print(f"Fetching {len(files)} asset(s) from {CONFIG['owner']}/{CONFIG['repo']}@{args.tag} -> {dest}")
    n_rel = n_fb = 0
    for f in files:
        where = _fetch_one(f, dest, args.tag)
        n_rel += where == "release"
        n_fb += where == "fallback"
        print(f"  + {f}  [{where}]")
    if n_fb:
        print(f"\nNote: {n_fb} asset(s) came from the bundled offline fallback "
              f"(release {args.tag} unreachable). Re-run with network to pin from the release.")
    print(f"Done. Commit these files into the poster repo's images/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
