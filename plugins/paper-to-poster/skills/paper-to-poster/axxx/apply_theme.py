#!/usr/bin/env python3
"""Apply the AXXX theme to a poster HTML (or a neutral posterly template).

AXXX-only skill (docs/adr/0001): instead of editing each template's :root by
hand, this appends ONE `<style id="axxx-theme">` at the end of <head>, after the
template's own <style>, so CSS source-order cascade overrides the design tokens
to the AXXX palette and adds the AXXX brand rules (top accent bar, arrow bullets,
affiliation-logo header). It also injects the Inter <link>. Idempotent: re-running
replaces the prior AXXX block rather than stacking.

The brand bullet rule references images/bullet_arrow.svg — run fetch_assets.py so
that file is present locally (no remote <img>; posterly `measure` gate stays green).

Usage:
  python axxx/apply_theme.py poster/poster.html
  python axxx/apply_theme.py templates/landscape_4col_neutral.html -o templates/landscape_4col_axxx.html
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" data-axxx-font>\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin data-axxx-font>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"'
    ' rel="stylesheet" data-axxx-font>'
)
STYLE_OPEN = '<style id="axxx-theme">'
STYLE_CLOSE = "</style>"


def _axxx_style_block() -> str:
    tokens = (HERE / "theme_tokens.css").read_text()
    brand = (HERE / "brand.css").read_text()
    # @import must be first in a stylesheet; we load Inter via <link> instead, so
    # drop the @import line from the appended block to keep it valid.
    brand = "\n".join(l for l in brand.splitlines() if not l.strip().startswith("@import"))
    return f"{STYLE_OPEN}\n{tokens}\n{brand}\n{STYLE_CLOSE}"


def _strip_prior(html: str) -> str:
    html = re.sub(r'<style id="axxx-theme">.*?</style>\s*', "", html, flags=re.DOTALL)
    html = re.sub(r'\s*<link[^>]*data-axxx-font[^>]*>', "", html)
    return html


def apply(html: str) -> str:
    html = _strip_prior(html)
    block = FONT_LINK + "\n" + _axxx_style_block() + "\n"
    if "</head>" not in html:
        raise SystemExit("error: no </head> in input HTML — not a poster document")
    return html.replace("</head>", block + "</head>", 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", help="poster/template HTML to theme (edited in place unless -o)")
    ap.add_argument("-o", "--output", help="write to this path instead of in place")
    args = ap.parse_args()

    src = Path(args.html)
    out = Path(args.output) if args.output else src
    out.write_text(apply(src.read_text()))
    print(f"AXXX theme applied -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
