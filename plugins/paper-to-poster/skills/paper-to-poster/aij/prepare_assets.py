#!/usr/bin/env python3
"""Copy the AIJ frame graphics into a poster's images/ directory.

The AIJ format's frame (gradient background with the white panel, and the AIJ
header mark) is bundled in the skill under aij/assets/ (docs/adr/0011). An AIJ
poster references them as images/aij_background.png and images/aij_mark.svg, so
copy them next to the poster — they are committed with the poster like any
other image, and the poster renders offline except for its web fonts.

The required AIRI five-year white logo is copied too. Fetch partner institutions
with `python axxx/fetch_assets.py --dest <poster>/images --logos <subset>`.

Usage:
  python aij/prepare_assets.py --dest poster/images
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAME_ASSETS = ("aij_background.png", "aij_mark.svg")


def prepare(dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    out = []
    for name in FRAME_ASSETS:
        target = dest / name
        shutil.copyfile(HERE / "assets" / name, target)
        out.append(target)
    logo = HERE.parent / "axxx" / "assets" / "airi_5_years_logo_white.svg"
    target = dest / logo.name
    shutil.copyfile(logo, target)
    out.append(target)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", required=True, help="the poster's images/ directory")
    args = ap.parse_args(argv)
    for p in prepare(Path(args.dest)):
        print(f"copied {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
