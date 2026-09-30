#!/usr/bin/env python3
"""Copy aij/fonts.css into the marked @font-face block of AIJ poster HTML files.

`aij/fonts.css` is the single source of the SB Sans Display CDN URLs
(docs/adr/0011). An AIJ poster carries a verbatim copy between the markers

    /* aij-fonts:begin */ ... /* aij-fonts:end */

inside its <style>, so the poster stays one self-contained HTML file. If the
CDN path ever moves, edit aij/fonts.css and re-run this on every AIJ poster
(and on templates/portrait_aij.html). Idempotent.

Usage:
  python aij/sync_fonts.py poster/poster.html [more.html ...]
  python aij/sync_fonts.py --check templates/portrait_aij.html   # exit 1 on drift
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEGIN = "/* aij-fonts:begin */"
END = "/* aij-fonts:end */"
_BLOCK = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)


def font_block() -> str:
    return f"{BEGIN}\n{(HERE / 'fonts.css').read_text().strip()}\n{END}"


def sync(html: str) -> str:
    if not _BLOCK.search(html):
        raise ValueError(f"no {BEGIN} ... {END} block found — not an AIJ poster?")
    return _BLOCK.sub(lambda _m: font_block(), html, count=1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", nargs="+", help="AIJ poster/template HTML file(s)")
    ap.add_argument("--check", action="store_true", help="report drift instead of rewriting (exit 1 if any)")
    args = ap.parse_args(argv)
    drift = False
    for p in map(Path, args.html):
        src = p.read_text()
        try:
            out = sync(src)
        except ValueError as e:
            print(f"error: {p}: {e}", file=sys.stderr)
            return 2
        if args.check:
            if out != src:
                print(f"DRIFT: {p} font block differs from aij/fonts.css")
                drift = True
        elif out != src:
            p.write_text(out)
            print(f"synced fonts -> {p}")
        else:
            print(f"up to date: {p}")
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
