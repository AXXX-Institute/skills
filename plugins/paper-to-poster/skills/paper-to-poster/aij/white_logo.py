#!/usr/bin/env python3
"""Make the white version of an affiliation logo for the AIJ footer.

The AIJ template shows affiliation logos in WHITE, straight on the gradient
footer (no plate behind them). The AXXX asset release ships colour logos, so
this derives the white version next to each one (`<name>_white.svg|png`):

  * SVG — every colour (fill, stroke, stop-color, CSS rules, the default black
    fill) becomes white, and white details drawn on coloured shapes (e.g. the
    letter inside HSE's blue emblem) become real cut-outs, so the mark stays
    readable instead of turning into a solid white blob (the artwork is used
    as a mask over a white fill). An all-white logo is left as is.
  * PNG/other rasters — every visible pixel becomes white, keeping its alpha;
    an opaque image without transparency gets alpha from its darkness (dark
    mark on a light background -> white mark on transparent).

Usage:
  python aij/white_logo.py poster/images/airi_logo.svg poster/images/hse_logo.svg
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WHITE = "#FFFFFF"
_WHITE_RE = re.compile(r"^(#fff|#ffffff|white|rgb\(\s*255\s*,\s*255\s*,\s*255\s*\))$", re.IGNORECASE)
_KEEP_RE = re.compile(r"^(none|transparent|inherit|currentcolor|url\(.*\))$", re.IGNORECASE)
_PAINT_PROPS = ("fill", "stroke", "stop-color", "color", "flood-color", "lighting-color")


def _classify(value: str) -> str:
    v = value.strip()
    if _KEEP_RE.match(v):
        return "keep"
    if _WHITE_RE.match(v):
        return "white"
    return "colour"


def whiten_svg(svg: str) -> str:
    """Return the white version of an SVG logo (see module docstring).

    The artwork becomes a luminance MASK over one white rectangle: inside the
    mask every colour is white (shown) and every white is black (cut out), in
    the artwork's own painting order — so white details drawn on top of a
    coloured shape become real holes (a knock-out), not a solid white blob."""
    from lxml import etree

    root = etree.fromstring(svg.encode() if isinstance(svg, str) else svg)
    svg_ns = root.nsmap.get(None, "http://www.w3.org/2000/svg")
    q = lambda t: f"{{{svg_ns}}}{t}"  # noqa: E731
    props = "|".join(_PAINT_PROPS)
    css_re = re.compile(rf"\b({props})\s*:\s*([^;\"'}}]+)", re.IGNORECASE)

    kinds = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        kinds += [_classify(el.get(a)) for a in _PAINT_PROPS if el.get(a) is not None]
        kinds += [_classify(m.group(2)) for m in css_re.finditer(el.get("style") or "")]
        if etree.QName(el).localname == "style":
            kinds += [_classify(m.group(2)) for m in css_re.finditer(el.text or "")]
    shapes = [el for el in root.iter() if isinstance(el.tag, str) and etree.QName(el).localname in
              ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "text", "use")]
    if shapes and "colour" not in kinds and "white" in kinds:
        return svg if isinstance(svg, str) else svg.decode()   # already an all-white logo

    def mask_value(value: str) -> str:
        kind = _classify(value)
        return value if kind == "keep" else ("#000000" if kind == "white" else WHITE)

    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for a in _PAINT_PROPS:
            if el.get(a) is not None:
                el.set(a, mask_value(el.get(a)))
        if el.get("style"):
            el.set("style", css_re.sub(lambda m: f"{m.group(1)}:{mask_value(m.group(2))}", el.get("style")))
        if etree.QName(el).localname == "style" and el.text:
            el.text = css_re.sub(lambda m: f"{m.group(1)}:{mask_value(m.group(2))}", el.text)

    vb = root.get("viewBox")
    if vb:
        x, y, w, h = (v for v in re.split(r"[\s,]+", vb.strip()))
    else:
        x, y = "0", "0"
        w = re.sub(r"[^0-9.]", "", root.get("width", "100")) or "100"
        h = re.sub(r"[^0-9.]", "", root.get("height", "100")) or "100"
        root.set("viewBox", f"0 0 {w} {h}")
    for a in ("fill", "color"):
        root.attrib.pop(a, None)
    mask = etree.Element(q("mask"), id="aij-white-mask", maskUnits="userSpaceOnUse", x=x, y=y, width=w, height=h)
    art = etree.SubElement(mask, q("g"), fill=WHITE, color=WHITE)   # unpainted shapes default to black -> shown
    for child in list(root):
        art.append(child)
    defs = etree.SubElement(root, q("defs"))
    defs.append(mask)
    etree.SubElement(root, q("rect"), x=x, y=y, width=w, height=h, fill=WHITE, mask="url(#aij-white-mask)")
    return etree.tostring(root, xml_declaration=True, encoding="utf-8").decode()


def whiten_raster(src: Path, dst: Path) -> None:
    from PIL import Image

    im = Image.open(src).convert("RGBA")
    alpha = im.getchannel("A")
    if alpha.getextrema()[0] == 255:   # fully opaque: derive alpha from darkness
        alpha = im.convert("L").point(lambda v: 255 - v)
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(alpha)
    white.save(dst)


def white_path(src: Path) -> Path:
    return src.with_name(f"{src.stem}_white{'.svg' if src.suffix.lower() == '.svg' else '.png'}")


def make_white(src: Path) -> Path:
    src = Path(src)
    dst = white_path(src)
    if src.suffix.lower() == ".svg":
        dst.write_text(whiten_svg(src.read_text()))
    else:
        whiten_raster(src, dst)
    return dst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logos", nargs="+", help="colour logo files (e.g. from axxx/fetch_assets.py)")
    args = ap.parse_args(argv)
    for f in args.logos:
        p = Path(f)
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 2
        print(f"white logo -> {make_white(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
