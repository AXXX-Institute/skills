#!/usr/bin/env python3
"""Make the white version of an affiliation logo for the AIJ footer.

The AIJ template shows affiliation logos in WHITE, straight on the gradient
footer (no plate behind them). The AXXX asset release ships colour logos, so
this derives the white version next to each one (`<name>_white.png`, or with
`--svg` a vector `<name>_white.svg`):

  * SVG — the artwork becomes a luminance mask over one white rectangle: every
    colour (fill, stroke, stop-color, CSS rules, the default black fill) shows
    as white, and white details painted on coloured shapes (e.g. the letter
    inside HSE's blue emblem) become real cut-outs, so the mark stays readable
    instead of turning into a solid white blob. Existing <mask>/<clipPath>
    content, `fill="none"` outlines and embedded <image>s (whitened by their
    alpha) keep working. An all-white logo, or one already produced by this
    tool, is left as is. The result is rendered (Chromium, transparent) to a
    600 px tall PNG — a masked SVG group can show a faint seam in some PDF
    viewers, a plain PNG with alpha cannot; `--svg` keeps the vector instead.
  * PNG/other rasters — every visible pixel becomes white, keeping its alpha;
    an opaque image gets its alpha from how far each pixel is from the
    background colour (so light-coloured marks stay solid too).

Usage:
  python aij/white_logo.py poster/images/airi_logo.svg poster/images/hse_logo.svg
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WHITE = "#FFFFFF"
MARKER = "data-aij-white"
_KEEP_RE = re.compile(r"^(none|transparent|inherit|initial|unset|currentcolor|context-fill|context-stroke|url\(.*\))$",
                      re.IGNORECASE)
_PAINT_PROPS = ("fill", "stroke", "stop-color", "color", "flood-color", "lighting-color")
#: Elements whose content is geometry for another element, not paint: never recoloured.
_NON_PAINT = ("mask", "clipPath")


def _split_important(value: str) -> tuple[str, str]:
    m = re.match(r"^(.*?)(\s*!\s*important)?\s*$", value.strip(), re.IGNORECASE | re.DOTALL)
    return m.group(1).strip(), (m.group(2) or "")


def _is_white(v: str) -> bool:
    v = v.strip().lower()
    if v == "white":
        return True
    m = re.fullmatch(r"#([0-9a-f]{3,8})", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        return len(h) in (6, 8) and h[:6] == "ffffff" and (len(h) == 6 or h[6:] == "ff")
    m = re.fullmatch(r"rgba?\(([^)]*)\)", v)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(1).strip()) if p]
        def chan(p):
            return float(p[:-1]) * 2.55 if p.endswith("%") else float(p)
        try:
            rgb_white = all(chan(p) >= 254.5 for p in parts[:3])
            alpha = (float(parts[3][:-1]) / 100 if parts[3].endswith("%") else float(parts[3])) if len(parts) > 3 else 1
        except ValueError:
            return False
        return rgb_white and alpha >= 0.99
    m = re.fullmatch(r"hsla?\(([^)]*)\)", v)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(1).strip()) if p]
        return len(parts) >= 3 and parts[2].rstrip("%") in ("100", "100.0")
    return False


def _classify(value: str) -> str:
    v, _imp = _split_important(value)
    if _KEEP_RE.match(v):
        return "keep"
    return "white" if _is_white(v) else "colour"


def whiten_svg(svg: str) -> str:
    """Return the white version of an SVG logo (see module docstring)."""
    from lxml import etree

    text = svg if isinstance(svg, str) else svg.decode()
    root = etree.fromstring(text.encode())
    if root.get(MARKER) is not None:
        return text                                   # already whitened by this tool
    svg_ns = root.nsmap.get(None, "http://www.w3.org/2000/svg")
    q = lambda t: f"{{{svg_ns}}}{t}"  # noqa: E731
    local = lambda el: etree.QName(el).localname  # noqa: E731
    props = "|".join(_PAINT_PROPS)
    css_re = re.compile(rf"(?<![\w-])({props})\s*:\s*([^;\"'}}]+)", re.IGNORECASE)

    def paintable(el) -> bool:
        return isinstance(el.tag, str) and not any(local(a) in _NON_PAINT for a in el.iterancestors()) \
            and local(el) not in _NON_PAINT

    kinds = []
    for el in root.iter():
        if not paintable(el):
            continue
        kinds += [_classify(el.get(a)) for a in _PAINT_PROPS if el.get(a) is not None]
        kinds += [_classify(m.group(2)) for m in css_re.finditer(el.get("style") or "")]
        if local(el) == "style":
            kinds += [_classify(m.group(2)) for m in css_re.finditer(el.text or "")]
    shapes = [el for el in root.iter() if paintable(el) and local(el) in
              ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "text", "use", "image")]
    if shapes and "colour" not in kinds and "white" in kinds and not any(local(s) == "image" for s in shapes):
        return text                                   # already an all-white logo

    def mask_value(value: str) -> str:
        v, imp = _split_important(value)
        kind = _classify(v)
        return value if kind == "keep" else ("#000000" if kind == "white" else WHITE) + imp

    for el in root.iter():
        if not paintable(el):
            continue
        for a in _PAINT_PROPS:
            if el.get(a) is not None:
                el.set(a, mask_value(el.get(a)))
        if el.get("style"):
            el.set("style", css_re.sub(lambda m: f"{m.group(1)}:{mask_value(m.group(2))}", el.get("style")))
        if local(el) == "style" and el.text:
            el.text = css_re.sub(lambda m: f"{m.group(1)}:{mask_value(m.group(2))}", el.text)

    existing_ids = {el.get("id") for el in root.iter() if isinstance(el.tag, str) and el.get("id")}
    def fresh(base: str) -> str:
        i, name = 0, base
        while name in existing_ids:
            i += 1
            name = f"{base}-{i}"
        existing_ids.add(name)
        return name
    mask_id, img_filter_id = fresh("aij-white-mask"), fresh("aij-white-image")

    # Embedded rasters: white wherever they are opaque (their alpha), inside the mask.
    images = [el for el in root.iter() if paintable(el) and local(el) == "image"]

    # The mask region and the white rectangle overshoot the visible area by 10% on
    # every side: the edge of a soft mask then lies outside the logo's viewport,
    # where some PDF rasterisers would otherwise draw a hairline along it.
    vb = root.get("viewBox")
    if vb:
        vx, vy, vw, vh = (float(v) for v in re.split(r"[\s,]+", vb.strip())[:4])
        x, y, w, h = (f"{v:g}" for v in (vx - 0.1 * vw, vy - 0.1 * vh, 1.2 * vw, 1.2 * vh))
    else:
        # No viewBox: user units are CSS px of the viewport; percentages cover it
        # whatever the width/height units are.
        x, y, w, h = "-10%", "-10%", "120%", "120%"
    mask = etree.Element(q("mask"), id=mask_id, maskUnits="userSpaceOnUse", x=x, y=y, width=w, height=h)
    if images:
        flt = etree.SubElement(mask, q("filter"), id=img_filter_id)
        etree.SubElement(flt, q("feColorMatrix"), type="matrix",
                         values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1 0")
        for im in images:
            im.set("filter", f"url(#{img_filter_id})")
    # Unpainted shapes default to black -> shown, unless the root itself sets a fill
    # (e.g. Figma's fill="none" for outline artwork), which the group then inherits.
    root_fill = root.get("fill") is not None or re.search(r"(?<![\w-])fill\s*:", root.get("style") or "")
    art = etree.SubElement(mask, q("g"), **({} if root_fill else {"fill": WHITE}), color=WHITE)
    for child in list(root):
        art.append(child)
    defs = etree.SubElement(root, q("defs"))
    defs.append(mask)
    etree.SubElement(root, q("rect"), x=x, y=y, width=w, height=h, mask=f"url(#{mask_id})",
                     style="fill:#FFFFFF !important;stroke:none !important;fill-opacity:1 !important;"
                           "opacity:1 !important;filter:none !important;visibility:visible !important")
    root.set(MARKER, "1")
    return etree.tostring(root, xml_declaration=True, encoding="utf-8").decode()


def whiten_raster(src: Path, dst: Path) -> None:
    from collections import Counter

    from PIL import Image, ImageChops

    im = Image.open(src).convert("RGBA")
    alpha = im.getchannel("A")
    if alpha.getextrema()[0] == 255:
        # Fully opaque: the background is the commonest edge colour; alpha = how far
        # each pixel is from it, stretched so the strongest mark pixel is opaque.
        rgb = im.convert("RGB")
        w, h = rgb.size
        edge = [rgb.getpixel((x, 0)) for x in range(w)] + [rgb.getpixel((x, h - 1)) for x in range(w)] \
            + [rgb.getpixel((0, y)) for y in range(h)] + [rgb.getpixel((w - 1, y)) for y in range(h)]
        bg = Counter(edge).most_common(1)[0][0]
        diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, bg))
        r, g, b = diff.split()
        dist = ImageChops.lighter(ImageChops.lighter(r, g), b)   # max channel distance: a yellow mark on white counts fully
        top = dist.getextrema()[1] or 1
        alpha = dist.point(lambda v: min(255, round(v * 255 / top)))
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(alpha)
    white.save(dst)


#: Height of the rendered white PNG. A footer logo prints at most 10.853mm tall,
#: so this is > 1400 dpi even at that size.
PNG_HEIGHT_PX = 600


def white_path(src: Path, svg: bool = False) -> Path:
    return src.with_name(f"{src.stem}_white{'.svg' if svg else '.png'}")


def render_svg_png(svg_text: str, dst: Path, height_px: int = PNG_HEIGHT_PX) -> None:
    """Rasterise an SVG with Chromium on a transparent page, `height_px` tall.

    The white SVG is a masked group; some PDF viewers draw a faint seam along the
    edge of such a group at certain zoom levels. A plain PNG with alpha has no
    such edge, so the white logo ships as a high-resolution PNG by default."""
    import tempfile

    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as d:
        svg_file = Path(d) / "logo.svg"
        svg_file.write_text(svg_text)
        page_file = Path(d) / "logo.html"
        page_file.write_text(
            "<!DOCTYPE html><html><head><style>html,body{margin:0;background:transparent}</style></head>"
            f'<body><img id="l" src="{svg_file.as_uri()}" style="display:block;height:{height_px}px;width:auto">'
            "</body></html>")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 8 * height_px, "height": height_px + 2})
                page.goto(page_file.as_uri())
                page.wait_for_function("() => document.getElementById('l').complete")
                page.locator("#l").screenshot(path=str(dst), omit_background=True)
            finally:
                browser.close()


def make_white(src: Path, svg: bool = False) -> Path:
    """Write the white version beside `src` and return its path.

    SVG logos are whitened (mask + knock-outs) and, by default, rendered to a
    high-resolution PNG `<name>_white.png`; `svg=True` keeps the vector
    `<name>_white.svg`. Rasters become `<name>_white.png`. A file this tool
    already produced is returned unchanged."""
    src = Path(src)
    if src.stem.endswith("_white"):
        return src
    if src.suffix.lower() == ".svg":
        out = whiten_svg(src.read_text())
        dst = white_path(src, svg=svg)
        if svg:
            dst.write_text(out)
        else:
            render_svg_png(out, dst)
        return dst
    dst = white_path(src)
    whiten_raster(src, dst)
    return dst


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logos", nargs="+", help="colour logo files (e.g. from axxx/fetch_assets.py)")
    ap.add_argument("--svg", action="store_true",
                    help="keep SVG logos as a white vector SVG instead of the default high-resolution PNG")
    args = ap.parse_args(argv)
    for f in args.logos:
        p = Path(f)
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 2
        print(f"white logo -> {make_white(p, svg=args.svg)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
