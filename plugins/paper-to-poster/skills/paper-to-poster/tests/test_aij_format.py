"""AIJ poster format: the scaffold, its frame fidelity, and its asset policy.

Static checks run everywhere. The render checks (computed type roles and frame
geometry vs. the organisers' .pptx) need Playwright/Chromium *and* network
access for the SB Sans Display web fonts (docs/adr/0011) — they skip otherwise.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE_HTML = SKILL / "templates" / "portrait_aij.html"
TEMPLATE_PPTX = SKILL / "aij" / "assets" / "aij_template.pptx"
FONTS_CSS = SKILL / "aij" / "fonts.css"
EXAMPLE = SKILL / "examples" / "compression_horizon_aij" / "poster.html"
sys.path.insert(0, str(SKILL / "aij"))

EMU_PER_MM = 36000
PX_PER_MM = 96 / 25.4

#: Texts from the organisers' template that are instructions, not content.
INSTRUCTION_SNIPPETS = (
    "В шапке шаблона", "В нижней части", "Пространство по центру",
    "Просьба не менять", "Шрифт заголовка", "Шрифт основного текста",
    "Ромашка", "december@mail.ru", "Пестель",
)


# --------------------------------------------------------------------------
# static
# --------------------------------------------------------------------------

def test_template_canvas_is_the_organisers_slide():
    html = TEMPLATE_HTML.read_text()
    assert re.search(r"@page\s*{\s*size:\s*190\.5mm\s+275\.2mm", html)
    with zipfile.ZipFile(TEMPLATE_PPTX) as z:
        pres = z.read("ppt/presentation.xml").decode()
    m = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', pres)
    assert (int(m.group(1)) / EMU_PER_MM, round(int(m.group(2)) / EMU_PER_MM, 1)) == (190.5, 275.2)


def test_template_font_block_matches_fonts_css():
    import sync_fonts

    html = TEMPLATE_HTML.read_text()
    assert sync_fonts.sync(html) == html, "run: python aij/sync_fonts.py templates/portrait_aij.html"
    assert EXAMPLE.exists()
    assert sync_fonts.sync(EXAMPLE.read_text()) == EXAMPLE.read_text()


def test_fonts_come_from_the_cdn_only():
    css = FONTS_CSS.read_text()
    urls = re.findall(r'url\("([^"]+)"\)', css)
    assert len(urls) == 3
    assert all(u.startswith("https://cdn-app.sberdevices.ru/") for u in urls)
    assert {w for w in re.findall(r"font-weight:\s*(\d+)", css)} == {"300", "400", "700"}


def test_no_font_binaries_in_the_skill():
    fonts = [p for p in SKILL.rglob("*")
             if p.suffix.lower() in (".woff", ".woff2", ".ttf", ".otf", ".eot", ".fntdata")]
    assert fonts == []


def test_bundled_template_has_its_embedded_fonts_stripped():
    with zipfile.ZipFile(TEMPLATE_PPTX) as z:
        names = z.namelist()
        pres = z.read("ppt/presentation.xml").decode()
        rels = z.read("ppt/_rels/presentation.xml.rels").decode()
        types = z.read("[Content_Types].xml").decode()
    assert not [n for n in names if n.startswith("ppt/fonts/")]
    assert "embeddedFont" not in pres and "embedTrueTypeFonts" not in pres
    assert "fonts/" not in rels and "fntdata" not in types
    # the frame survives: background + AIJ mark
    assert "ppt/media/image1.png" in names and "ppt/media/image6.svg" in names


def test_template_has_no_pptx_instructions_and_keeps_the_number_placeholder():
    html = TEMPLATE_HTML.read_text()
    for s in INSTRUCTION_SNIPPETS:
        assert s not in html
    assert "№TODO" in html
    assert 'data-measure-role="poster"' in html and 'data-measure-role="footer"' in html


def test_prepare_assets_copies_the_frame(tmp_path):
    import prepare_assets

    out = prepare_assets.prepare(tmp_path / "images")
    assert sorted(p.name for p in out) == ["aij_background.png", "aij_mark.svg"]
    assert all(p.stat().st_size > 0 for p in out)


def test_sync_fonts_rewrites_a_stale_block(tmp_path):
    import sync_fonts

    stale = TEMPLATE_HTML.read_text().replace("SBSansDisplay-Light.woff2", "OLD-Light.woff2")
    p = tmp_path / "poster.html"
    p.write_text(stale)
    assert sync_fonts.main(["--check", str(p)]) == 1
    assert sync_fonts.main([str(p)]) == 0
    assert "OLD-Light" not in p.read_text()
    assert sync_fonts.main(["--check", str(p)]) == 0


# --------------------------------------------------------------------------
# rendered
# --------------------------------------------------------------------------

def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


def _cdn_reachable() -> bool:
    url = re.search(r'url\("([^"]+)"\)', FONTS_CSS.read_text()).group(1)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=8) as r:
            return r.status == 200
    except Exception:
        return False


needs_render = pytest.mark.skipif(
    not (_chromium_available() and _cdn_reachable()),
    reason="needs playwright+chromium and network access to the SB Sans Display CDN",
)


@pytest.fixture(scope="module")
def scaffold_dir(tmp_path_factory):
    import prepare_assets

    d = tmp_path_factory.mktemp("aij_scaffold")
    shutil.copyfile(TEMPLATE_HTML, d / "poster.html")
    prepare_assets.prepare(d / "images")
    return d


def _render(html: Path, js: str):
    sys.path.insert(0, str(SKILL / "tools"))
    from _posterly import canvas as _canvas, render as _r
    from playwright.sync_api import sync_playwright

    _, viewport = _canvas.resolve_canvas(html, None, label="[test]")
    with sync_playwright() as p:
        browser, _ctx, page = _r.open_print_emulated_page(p, viewport)
        try:
            page.goto(html.as_uri())
            page.wait_for_load_state("networkidle")
            _r.settle_page(page)
            return page.evaluate(js)
        finally:
            browser.close()


_STYLE_JS = """
() => {
  const pick = (sel) => { const el = document.querySelector(sel); const s = getComputedStyle(el);
    return {family: s.fontFamily, weight: s.fontWeight, size: parseFloat(s.fontSize)}; };
  return {
    fonts: ['300','400','700'].map(w => document.fonts.check(w + ' 10px "SB Sans Display"')),
    title: pick('.aij-title'), number: pick('.aij-number'), authors: pick('.aij-authors'),
    heading: pick('.section-title'), body: pick('.section p'), li: pick('.section li'),
    caption: pick('.caption'), th: pick('.result-table th'), td: pick('.result-table td'),
    affiliations: pick('.aij-affiliations'), contact: pick('.aij-contact'),
  };
}
"""

PT = 96 / 72  # px per pt


@needs_render
def test_type_roles_render_in_sb_sans_display(scaffold_dir):
    got = _render(scaffold_dir / "poster.html", _STYLE_JS)
    assert got["fonts"] == [True, True, True], "SB Sans Display Light/Regular/Bold did not load"
    roles = {  # element -> (weight, pt)
        "title": ("700", 14), "number": ("700", 14),
        "authors": ("400", 7), "heading": ("400", 7), "th": ("400", 7),
        "body": ("300", 7), "li": ("300", 7), "caption": ("300", 7), "td": ("300", 7),
        "affiliations": ("300", 7), "contact": ("300", 7),
    }
    for key, (weight, pt) in roles.items():
        el = got[key]
        assert el["family"].startswith('"SB Sans Display"'), (key, el)
        assert el["weight"] == weight, (key, el)
        assert el["size"] == pytest.approx(pt * PT, abs=0.05), (key, el)


def _pptx_frame() -> dict[str, tuple[float, float, float, float]]:
    """name -> (x, y, w, h) in mm, from the organisers' template; group
    children resolved to slide coordinates."""
    from pptx import Presentation

    prs = Presentation(str(TEMPLATE_PPTX))
    out = {}

    def walk(shapes, dx=0, dy=0):
        for s in shapes:
            if s.shape_type == 6:  # group
                xfrm = s._element.grpSpPr.find(
                    "{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm")
                off, choff = xfrm[0], xfrm[2]
                walk(s.shapes, dx + int(off.get("x")) - int(choff.get("x")),
                     dy + int(off.get("y")) - int(choff.get("y")))
            else:
                out[s.name] = tuple(v / EMU_PER_MM for v in (s.left + dx, s.top + dy, s.width, s.height))
    walk(prs.slides[0].shapes)
    return out


_FRAME_JS = """
() => {
  const P = document.querySelector('.poster').getBoundingClientRect();
  const r = (sel) => { const el = document.querySelector(sel); if (!el) return null;
    const b = el.getBoundingClientRect(); return [b.x - P.x, b.y - P.y, b.width, b.height]; };
  return {bg: r('.aij-bg'), mark: r('.aij-mark'), number: r('.aij-number'), title: r('.aij-title'),
          authors: r('.aij-authors'), affiliations: r('.aij-affiliations'), contact: r('.aij-contact'),
          qr: r('.aij-qr'), logos: r('.aij-logos')};
}
"""

INSET_MM = 1.27  # PowerPoint's default top inset for the template's text boxes


@needs_render
@pytest.mark.parametrize("which", ["scaffold", "example"])
def test_frame_sits_on_the_pptx_coordinates(which, scaffold_dir):
    html = scaffold_dir / "poster.html" if which == "scaffold" else EXAMPLE
    got = {k: (tuple(v / PX_PER_MM for v in b) if b else None) for k, b in _render(html, _FRAME_JS).items()}
    ref = _pptx_frame()
    tol = 1.0

    def near(a, b):
        return all(abs(x - y) <= tol for x, y in zip(a, b))

    assert near(got["bg"], ref["Рисунок 10"]), got["bg"]
    assert near(got["mark"], ref["Рисунок 8"]), got["mark"]
    for key, name in (("number", "TextBox 70"), ("title", "TextBox 2"), ("authors", "TextBox 9"),
                      ("affiliations", "TextBox 31"), ("contact", "TextBox 34")):
        x, y, _w, _h = ref[name]
        assert near(got[key][:2], (x, y + INSET_MM)), (key, got[key][:2], (x, y + INSET_MM))
    lx, ly = ref["Рисунок 13"][:2]            # first sample-logo slot
    assert near(got["logos"][:1], (lx,)), got["logos"]
    if which == "example":                    # one QR -> the outer tile
        assert near(got["qr"], ref["Скругленный прямоугольник 66"]), got["qr"]


@needs_render
def test_example_pdf_embeds_sb_sans_display():
    pdf = EXAMPLE.with_name("poster.pdf")
    assert pdf.exists()
    if not shutil.which("pdffonts"):
        pytest.skip("pdffonts (poppler-utils) not installed")
    fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True, check=True).stdout
    for face in ("SBSansDisplay-Light", "SBSansDisplay-Regular", "SBSansDisplay-Bold"):
        assert face in fonts, fonts


@needs_render
def test_scaffold_passes_preflight(scaffold_dir):
    r = subprocess.run([sys.executable, str(SKILL / "tools" / "poster_check.py"), "preflight",
                        str(scaffold_dir / "poster.html")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


@needs_render
@pytest.mark.parametrize("gate", ["preflight", "measure", "polish"])
def test_example_passes_gates(gate):
    args = [sys.executable, str(SKILL / "tools" / "poster_check.py"), gate, str(EXAMPLE)]
    if gate == "polish":
        args.append("--strict")
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


@needs_render
def test_example_pdf_passes_verify_final():
    r = subprocess.run([sys.executable, str(SKILL / "tools" / "poster_check.py"), "verify-final",
                        str(EXAMPLE.with_name("poster.pdf")), "--from-html", str(EXAMPLE)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
