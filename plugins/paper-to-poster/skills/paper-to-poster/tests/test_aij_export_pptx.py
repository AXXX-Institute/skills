"""AIJ .pptx export (aij/export_pptx.py, docs/adr/0012) — automated checks only.

The exported file is re-read with python-pptx/lxml and compared against the
Chromium render of the same HTML: every text block becomes a native text frame
with the same text, font name, size and weight at the same place (±0.5 mm);
tables are native tables; figures are pictures; every formula is a native
Office equation (OMML, validated against the ECMA-376 math schema) wrapped in
mc:AlternateContent with a picture fallback; a formula that cannot be
converted degrades to a picture and is reported.

Needs the [pptx] extra (python-pptx, mathml2omml, lxml, fonttools, brotli), Playwright/Chromium,
and network access (SB Sans Display CDN + MathJax CDN); skips otherwise.
"""
from __future__ import annotations

import copy
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
EXAMPLE = SKILL / "examples" / "compression_horizon_aij" / "poster.html"
XSD = Path(__file__).resolve().parent / "fixtures" / "ooxml_math" / "shared-math.xsd"
sys.path.insert(0, str(SKILL / "aij"))
sys.path.insert(0, str(SKILL / "tools"))

pptx = pytest.importorskip("pptx")
etree = pytest.importorskip("lxml.etree")
pytest.importorskip("mathml2omml")

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}
EMU_PER_MM = 36000
#: sha256 of the unmodified files in OfficeOpenXML-XMLSchema-Transitional.zip.
ECMA_SHA256 = {
    "shared-math.xsd": "132e44dc10f2959e3f585584e5d82e7b2e329691e3010646e497710bd9774152",
    "shared-commonSimpleTypes.xsd": "48675c4f82f6b097434d4b7e313635b790257cca58fa90dd0e8f19c9affa18ed",
}
PX_PER_MM = 96 / 25.4
TOL_MM = 0.5


def _env_ok() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            p.chromium.launch().close()
        url = re.search(r'url\("([^"]+)"\)', (SKILL / "aij" / "fonts.css").read_text()).group(1)
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=8) as r:
            return r.status == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _env_ok(), reason="needs chromium + network (fonts/MathJax CDN)")


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    import export_pptx

    out = tmp_path_factory.mktemp("aij_export") / "poster.pptx"
    report = export_pptx.export(EXAMPLE, out)
    return out, report


@pytest.fixture(scope="module")
def slide_xml(exported):
    out, _ = exported
    with zipfile.ZipFile(out) as z:
        return etree.fromstring(z.read("ppt/slides/slide1.xml"))


_BLOCKS_JS = """
() => {
  const P = document.querySelector('.poster').getBoundingClientRect();
  const text = (el) => { const c = el.cloneNode(true);
    c.querySelectorAll('mjx-container').forEach(m => m.remove());
    return c.textContent.replace(/\\s+/g, ' ').trim(); };
  const box = (el) => { const b = el.getBoundingClientRect(), s = getComputedStyle(el);
    const pl = parseFloat(s.paddingLeft) + parseFloat(s.borderLeftWidth);
    const pt = parseFloat(s.paddingTop) + parseFloat(s.borderTopWidth);
    return [b.x - P.x + pl, b.y - P.y + pt]; };
  const sel = '.aij-number, .aij-title, .aij-authors, .aij-affiliations, .aij-contact, '
            + '.section-title, .section-subtitle, .section > p, .figure .caption';
  const runs = (el) => { const out = [];
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      if (n.parentElement.closest('mjx-container') || !n.nodeValue.trim()) continue;
      const pe = n.parentElement, s = getComputedStyle(pe);
      const sup = pe.closest('sup, sub');
      out.push({text: n.nodeValue.replace(/\\s+/g, ' ').trim(), weight: parseInt(s.fontWeight, 10), family: s.fontFamily,
                px: parseFloat(getComputedStyle(sup ? sup.parentElement : pe).fontSize)}); }
    return out; };
  const blocks = [...document.querySelectorAll(sel)].map(el => {
    const s = getComputedStyle(el);
    return {text: text(el), pos: box(el), weight: s.fontWeight, px: parseFloat(s.fontSize), runs: runs(el)}; });
  const lists = [...document.querySelectorAll('.section > ul')].map(ul => ({
    items: [...ul.children].map(li => text(li)), pos: [ul.getBoundingClientRect().x - P.x, ul.getBoundingClientRect().y - P.y]}));
  const tables = [...document.querySelectorAll('table')].map(t => ({
    pos: [t.getBoundingClientRect().x - P.x, t.getBoundingClientRect().y - P.y],
    cells: [...t.rows].map(r => [...r.cells].map(c => text(c)))}));
  const images = [...document.querySelectorAll('img')].filter(i => !i.classList.contains('aij-bg') && !i.classList.contains('aij-mark'))
    .map(i => { const b = i.getBoundingClientRect(); return [b.x - P.x, b.y - P.y, b.width, b.height]; });
  const math = MathJax.startup.document.getMathItemsWithin(document.body).map(it => ({display: !!it.display, tex: it.math}));
  return {blocks, lists, tables, images, math};
}
"""


@pytest.fixture(scope="module")
def html_facts():
    from _posterly import canvas as _canvas, render as _r
    from playwright.sync_api import sync_playwright

    _, viewport = _canvas.resolve_canvas(EXAMPLE, None, label="[test]")
    with sync_playwright() as p:
        browser, _ctx, page = _r.open_print_emulated_page(p, viewport)
        try:
            page.goto(EXAMPLE.as_uri())
            page.wait_for_load_state("networkidle")
            _r.settle_page(page)
            return page.evaluate(_BLOCKS_JS)
        finally:
            browser.close()


def _sps(slide_xml):
    """Every text-bearing p:sp, resolving mc:AlternateContent to its Choice."""
    out = []
    for sp in slide_xml.iter(f"{{{NS['p']}}}sp"):
        if sp.getparent().tag == f"{{{NS['mc']}}}Fallback":
            continue
        tx = sp.find("p:txBody", NS)
        if tx is None:
            continue
        paras = []
        for p in tx.findall("a:p", NS):
            paras.append("".join(t.text or "" for t in p.iter(f"{{{NS['a']}}}t")
                                 if not any(a.tag == f"{{{NS['m']}}}oMath" for a in t.iterancestors())))
        off = sp.find("p:spPr/a:xfrm/a:off", NS)
        out.append({"el": sp, "paras": paras, "text": " ".join(p for p in paras if p),
                    "x": int(off.get("x")) / EMU_PER_MM, "y": int(off.get("y")) / EMU_PER_MM})
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


# --------------------------------------------------------------------------
# structure
# --------------------------------------------------------------------------

def test_one_slide_on_the_organisers_canvas(exported):
    out, _ = exported
    prs = pptx.Presentation(str(out))
    assert (prs.slide_width, prs.slide_height) == (6858000, 9907588)
    assert len(prs.slides) == 1


def test_every_run_typeface_is_embedded(exported, slide_xml):
    """PowerPoint shows a substitute (Calibri) for fonts that are neither
    installed nor embedded: every typeface the text uses must be embedded, as
    EOT parts whose font really is that family (docs/adr/0013)."""
    import io

    import embed_fonts
    from fontTools.ttLib import TTFont

    out, report = exported
    used = {r.get("typeface") for r in slide_xml.iter(f"{{{NS['a']}}}latin")} - {"Cambria Math"}
    assert used == {"SB Sans Display", "SB Sans Display Light", "SB Sans Display Semibold",
                    "SB Sans Text", "SB Sans Text Semibold"}
    assert set(report.fonts_embedded) == used
    with zipfile.ZipFile(out) as z:
        pres = etree.fromstring(z.read("ppt/presentation.xml"))
        assert pres.get("embedTrueTypeFonts") == "1"
        rels = etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels}
        slots = {}
        for ef in pres.find("p:embeddedFontLst", NS):
            face = ef.find("p:font", NS).get("typeface")
            for slot in ef[1:]:
                eot = embed_fonts.parse_eot(z.read("ppt/" + target[slot.get(f"{{{NS['r']}}}id")]))
                ttf = TTFont(io.BytesIO(eot["font_data"]))
                assert eot["version"] == 0x00020002 and eot["magic"] == 0x504C and eot["fsType"] == 0
                assert eot["family"] == face == ttf["name"].getDebugName(1)
                slots[(face, etree.QName(slot).localname)] = ttf["OS/2"].usWeightClass
    assert slots == {("SB Sans Display Light", "regular"): 300, ("SB Sans Display", "regular"): 400,
                     ("SB Sans Display Semibold", "regular"): 600, ("SB Sans Display", "bold"): 700,
                     ("SB Sans Text", "regular"): 400, ("SB Sans Text Semibold", "regular"): 600}


def test_gallery_pptx_carries_the_fonts():
    """The published example embeds its fonts too (maintainers' decision,
    docs/adr/0013), so it opens in SB Sans Display anywhere."""
    with zipfile.ZipFile(EXAMPLE.with_name("poster.pptx")) as z:
        assert len([n for n in z.namelist() if n.startswith("ppt/fonts/")]) == 6
        assert 'embedTrueTypeFonts="1"' in z.read("ppt/presentation.xml").decode()


def test_eot_round_trip_keeps_the_font_bytes():
    import embed_fonts

    faces = embed_fonts.fetch_faces()
    for f in faces:
        eot = embed_fonts.ttf_to_eot(f.ttf)
        h = embed_fonts.parse_eot(eot)
        assert h["size"] == len(eot) and h["font_data"] == f.ttf


def test_no_embed_fonts_option(tmp_path):
    import export_pptx

    out = tmp_path / "plain.pptx"
    report = export_pptx.export(EXAMPLE, out, embed_fonts=False)
    assert report.fonts_embedded == []
    with zipfile.ZipFile(out) as z:
        assert not [n for n in z.namelist() if n.startswith("ppt/fonts/")]
        assert "embeddedFont" not in z.read("ppt/presentation.xml").decode()


def test_footer_logos_are_transparent_pictures(exported):
    """White logos sit straight on the gradient: their pictures must be
    transparent around the mark, not a patch of the page behind them."""
    import io

    from PIL import Image

    out, _ = exported
    prs = pptx.Presentation(str(out))
    logos = [s for s in prs.slides[0].shapes if s.shape_type == 13 and 255 < s.top / EMU_PER_MM < 268
             and 74 < s.left / EMU_PER_MM < 147]
    assert len(logos) == 3
    for s in logos:
        alpha = Image.open(io.BytesIO(s.image.blob)).convert("RGBA").getchannel("A")
        assert alpha.getextrema()[0] == 0


def test_package_thumbnail_is_the_poster_not_the_template(exported):
    out, _ = exported
    tpl = SKILL / "aij" / "assets" / "aij_template.pptx"
    with zipfile.ZipFile(out) as z, zipfile.ZipFile(tpl) as t:
        assert z.read("docProps/thumbnail.jpeg") != t.read("docProps/thumbnail.jpeg")


def test_frame_background_and_mark_kept_instructions_removed(exported, slide_xml):
    out, _ = exported
    prs = pptx.Presentation(str(out))
    names = [s.name for s in prs.slides[0].shapes]
    assert "Рисунок 10" in names and "Рисунок 8" in names
    all_text = "".join(t.text or "" for t in slide_xml.iter(f"{{{NS['a']}}}t"))
    for s in ("В шапке шаблона", "Пространство по центру", "Просьба не менять", "Ромашка", "Шрифт заголовка"):
        assert s not in all_text


def test_every_text_block_is_native_text_at_its_rendered_place(html_facts, slide_xml):
    sps = _sps(slide_xml)
    for b in html_facts["blocks"]:
        want = _norm(b["text"])
        match = [s for s in sps if _norm(s["text"]) == want]
        assert match, f"no native text frame for {want[:60]!r}"
        x_mm, y_mm = (v / PX_PER_MM for v in b["pos"])
        assert any(abs(s["x"] - x_mm) <= TOL_MM and abs(s["y"] - y_mm) <= TOL_MM for s in match), \
            (want[:40], x_mm, y_mm, [(s["x"], s["y"]) for s in match])


def _expected_face(weight: int, family: str) -> tuple[str, bool]:
    if "SB Sans Text" in family:
        return ("SB Sans Text Semibold" if weight >= 550 else "SB Sans Text"), False
    if weight <= 350:
        return "SB Sans Display Light", False
    if 550 <= weight < 650:
        return "SB Sans Display Semibold", False
    return "SB Sans Display", weight >= 650


def test_each_block_keeps_its_role_font_size_and_weight(html_facts, slide_xml):
    """Per block, every text run in the pptx carries the typeface, size and bold
    flag of the HTML text it came from (Title 13pt Semibold, Subtitle 7pt Regular,
    Body 7pt Light, <strong> Bold, keywords Regular)."""
    sps = _sps(slide_xml)
    for b in html_facts["blocks"]:
        sp = next(s for s in sps if _norm(s["text"]) == _norm(b["text"]))
        pptx_runs = []
        for r in sp["el"].iter(f"{{{NS['a']}}}r"):
            if any(a.tag == f"{{{NS['m']}}}oMath" for a in r.iterancestors()):
                continue
            rpr = r.find("a:rPr", NS)
            pptx_runs.append((_norm(r.find("a:t", NS).text or ""), rpr.find("a:latin", NS).get("typeface"),
                              int(rpr.get("sz")), rpr.get("b") == "1"))
        for hr in b["runs"]:
            want_face, want_bold = _expected_face(hr["weight"], hr["family"])
            want_sz = int(round(hr["px"] * 0.75 * 100))
            match = [r for r in pptx_runs if r[0] == _norm(hr["text"])]
            assert match, (b["text"][:40], hr["text"])
            assert (match[0][1], match[0][2], match[0][3]) == (want_face, want_sz, want_bold), (hr, match[0])


def test_lists_are_one_bulleted_frame_each(html_facts, slide_xml):
    sps = _sps(slide_xml)
    for ul in html_facts["lists"]:
        items = [_norm(i) for i in ul["items"]]
        match = [s for s in sps if [_norm(p) for p in s["paras"]] == items]
        assert match, items
        s = match[0]
        x_mm, y_mm = (v / PX_PER_MM for v in ul["pos"])
        assert abs(s["x"] - x_mm) <= TOL_MM and abs(s["y"] - y_mm) <= TOL_MM
        for p in s["el"].iter(f"{{{NS['a']}}}p"):
            assert p.find("a:pPr/a:buChar", NS) is not None


def test_fonts_sizes_and_weights_follow_content_and_frame_roles(slide_xml):
    allowed = {("SB Sans Display Semibold",1300,False),
               ("SB Sans Display",700,False), ("SB Sans Display Light",700,False),
               ("SB Sans Display",1400,True), ("SB Sans Display Semibold",1000,False),
               ("SB Sans Text",700,False), ("SB Sans Text Semibold",700,False)}
    seen = set()
    for r in slide_xml.iter(f"{{{NS['a']}}}r"):
        rpr = r.find("a:rPr", NS)
        seen.add((rpr.find("a:latin", NS).get("typeface"),int(rpr.get("sz")),rpr.get("b") == "1"))
    assert seen == allowed
    # Captions and every table run remain regular, even highlighted cells.
    for rpr in slide_xml.findall('.//a:tbl//a:rPr', NS):
        assert rpr.find('a:latin', NS).get('typeface') == 'SB Sans Text'
        assert rpr.get('sz') == '700' and rpr.get('b') != '1'


def test_title_and_number_texts(slide_xml):
    texts = {_norm(s["text"]) for s in _sps(slide_xml)}
    assert "№1" in texts and "№TODO" not in texts
    assert "Progressive Cramming: Reliable Token Compression and What It Reveals" in texts


def test_tables_are_native_with_matching_cells(exported, html_facts):
    out, report = exported
    prs = pptx.Presentation(str(out))
    tables = [s for s in prs.slides[0].shapes if s.has_table]
    assert len(tables) == len(html_facts["tables"]) == report.tables
    for want in html_facts["tables"]:
        x_mm, y_mm = (v / PX_PER_MM for v in want["pos"])
        t = min(tables, key=lambda s: abs(s.left / EMU_PER_MM - x_mm) + abs(s.top / EMU_PER_MM - y_mm))
        assert abs(t.left / EMU_PER_MM - x_mm) <= TOL_MM and abs(t.top / EMU_PER_MM - y_mm) <= TOL_MM
        got = [[_norm(t.table.cell(r, c).text) for c in range(len(want["cells"][r]))] for r in range(len(want["cells"]))]
        assert got == [[_norm(c) for c in row] for row in want["cells"]]


def test_every_figure_logo_and_qr_is_a_picture_in_place(exported, html_facts):
    out, _ = exported
    prs = pptx.Presentation(str(out))
    pics = [(s.left / EMU_PER_MM, s.top / EMU_PER_MM, s.width / EMU_PER_MM, s.height / EMU_PER_MM)
            for s in prs.slides[0].shapes if s.shape_type == 13 and s.name not in ("Рисунок 10", "Рисунок 8")]
    for img in html_facts["images"]:
        want = [v / PX_PER_MM for v in img]
        assert any(all(abs(a - b) <= TOL_MM for a, b in zip(p, want)) for p in pics), want


# --------------------------------------------------------------------------
# math
# --------------------------------------------------------------------------

def test_every_formula_is_a_native_equation_with_a_fallback(exported, html_facts, slide_xml):
    _, report = exported
    n_math = len(html_facts["math"])
    assert n_math >= 2 and any(m["display"] for m in html_facts["math"])
    ms = list(slide_xml.iter(f"{{{NS['a14']}}}m"))
    assert len(ms) == n_math
    assert report.equations_native + report.equations_inline_native == n_math
    assert report.equations_as_picture == [] and report.frames_as_picture == []
    assert report.warnings == []
    for m in ms:
        choice = next(a for a in m.iterancestors() if a.tag == f"{{{NS['mc']}}}Choice")
        assert choice.get("Requires") == "a14"
        fallback = choice.getnext()
        assert fallback.tag == f"{{{NS['mc']}}}Fallback"
        blip = fallback.find(".//a:blipFill/a:blip", NS)
        assert blip is not None and blip.get(f"{{{NS['r']}}}embed")


def _omml_roots(slide_xml):
    for om in slide_xml.iter(f"{{{NS['m']}}}oMathPara", f"{{{NS['m']}}}oMath"):
        if om.tag.endswith("}oMath") and om.getparent().tag == f"{{{NS['m']}}}oMathPara":
            continue
        yield om


def _schema():
    """ECMA-376 shared-math.xsd, byte-identical to Ecma's file; its WordprocessingML
    and xml: imports are pointed at the local stubs in memory (the Ecma notice
    forbids editing the file itself)."""
    src = XSD.read_text()
    src = src.replace('schemaLocation="wml.xsd"', 'schemaLocation="wml-stub.xsd"')
    src = src.replace('<xsd:import namespace="http://www.w3.org/XML/1998/namespace"/>',
                      '<xsd:import namespace="http://www.w3.org/XML/1998/namespace" schemaLocation="xml-stub.xsd"/>')
    assert "wml-stub.xsd" in src and "xml-stub.xsd" in src
    doc = etree.fromstring(src.encode(), base_url=XSD.as_uri())
    return etree.XMLSchema(etree.ElementTree(doc))


def test_vendored_ecma_schemas_are_unmodified():
    """The Ecma copyright notice forbids modifying the schema files: pin their
    content (sha256 of the files in ECMA-376 Part 4 Transitional, 5th ed.)."""
    import hashlib

    got = {f: hashlib.sha256((XSD.parent / f).read_bytes()).hexdigest()
           for f in ("shared-math.xsd", "shared-commonSimpleTypes.xsd")}
    assert got == ECMA_SHA256, got


def _strip_drawingml(om):
    """PowerPoint carries run formatting as <a:rPr> inside <m:r>; that is the
    DrawingML host's extension, not OMML, so validate the math without it."""
    c = copy.deepcopy(om)
    for rpr in list(c.iter(f"{{{NS['a']}}}rPr")):
        rpr.getparent().remove(rpr)
    return c


def test_omml_validates_against_the_ecma_math_schema(slide_xml):
    schema = _schema()
    roots = list(_omml_roots(slide_xml))
    assert roots
    for om in roots:
        assert schema.validate(_strip_drawingml(om)), (etree.tostring(om)[:300], schema.error_log)


def test_math_runs_carry_cambria_math(slide_xml):
    for r in slide_xml.iter(f"{{{NS['m']}}}r"):
        rpr = r.find("a:rPr", NS)
        assert rpr is not None and rpr.find("a:latin", NS).get("typeface") == "Cambria Math"


@pytest.mark.parametrize("tex", [
    r"\sqrt{x}", r"\frac{a+b}{c}", r"x_i^2", r"\sum_{i=1}^{n} x_i", r"\mathbf{e} = W\mathbf{z} + \mathbf{b}",
    r"\hat{\theta}", r"\left(\frac{1}{2}\right)", r"\mathbb{R}^{d \times k}", r"\sqrt[3]{y}",
])
def test_common_constructs_convert_to_valid_omml(tex, tmp_path):
    """MathJax -> MathML -> OMML for constructs posters use; each must validate
    (normalize_omml repairs mathml2omml's missing <m:deg> for plain \\sqrt)."""
    import export_pptx
    from playwright.sync_api import sync_playwright

    html = tmp_path / "m.html"
    html.write_text(
        "<html><head><script>window.MathJax={tex:{inlineMath:[['$','$']]}}</script>"
        "<script src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'></script></head>"
        f"<body><p>${tex}$</p></body></html>")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(html.as_uri())
        pg.wait_for_function("() => window.MathJax && MathJax.startup && MathJax.startup.promise")
        mml = pg.evaluate("() => MathJax.startup.promise.then(() => "
                          "MathJax.startup.toMML(MathJax.startup.document.getMathItemsWithin(document.body)[0].root))")
        b.close()
    om = export_pptx._default_mathml_to_omml(mml)
    assert _schema().validate(om), (tex, etree.tostring(om), _schema().error_log)


def test_conversion_failure_degrades_to_picture_and_is_reported(tmp_path, html_facts):
    import export_pptx

    def broken(_mml):
        raise ValueError("forced failure")

    out = tmp_path / "broken.pptx"
    report = export_pptx.export(EXAMPLE, out, mathml_to_omml=broken)
    n_math = len(html_facts["math"])
    assert len(report.equations_as_picture) == n_math
    assert all("forced failure" in f["error"] for f in report.equations_as_picture)
    assert report.equations_native == report.equations_inline_native == 0
    assert report.frames_as_picture  # paragraphs whose inline formula failed
    with zipfile.ZipFile(out) as z:
        xml = z.read("ppt/slides/slide1.xml").decode()
    assert "a14:m" not in xml and "oMath" not in xml


def test_refuses_a_non_aij_poster(tmp_path):
    import export_pptx

    with pytest.raises(SystemExit, match="not an AIJ poster"):
        export_pptx.export(SKILL / "templates" / "portrait_2col_axxx.html", tmp_path / "x.pptx")


# --------------------------------------------------------------------------
# edge cases (tests/aij_edge_poster.py): math in tables, TeX errors, graphics,
# mixed content — nothing may vanish silently
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def edge(tmp_path_factory):
    import aij_edge_poster
    import export_pptx

    d = tmp_path_factory.mktemp("aij_edge")
    html = aij_edge_poster.build(d)
    out = d / "edge.pptx"
    report = export_pptx.export(html, out)
    with zipfile.ZipFile(out) as z:
        xml = etree.fromstring(z.read("ppt/slides/slide1.xml"))
    return html, out, report, xml


def _math_count(html: Path) -> int:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(html.as_uri())
        pg.wait_for_function("() => window.MathJax && MathJax.startup && MathJax.startup.promise")
        n = pg.evaluate("() => MathJax.startup.promise.then(() => "
                        "MathJax.startup.document.getMathItemsWithin(document.body).length)")
        b.close()
    return n


def test_edge_every_formula_is_accounted_for(edge):
    html, _, report, _ = edge
    n = _math_count(html)
    assert n == 6   # \alpha, 0.1, 91.2 \pm 0.3, \foo{x}, x^2, \textcolor{red}{\foo}
    native = report.equations_native + report.equations_inline_native
    assert native + len(report.equations_as_picture) == n


def test_edge_table_with_math_is_native_with_a_picture_fallback(edge):
    _, _, report, xml = edge
    frames = [gf for gf in xml.iter(f"{{{NS['p']}}}graphicFrame") if gf.find(".//a:tbl", NS) is not None]
    assert len(frames) == 1 and report.tables == 1
    gf = frames[0]
    choice = gf.getparent()
    assert choice.tag == f"{{{NS['mc']}}}Choice" and choice.get("Requires") == "a14"
    assert len(list(gf.iter(f"{{{NS['a14']}}}m"))) == 3        # \alpha, 0.1, 91.2 \pm 0.3
    fb = choice.getnext()
    assert fb.tag == f"{{{NS['mc']}}}Fallback"
    pic = fb.find("p:pic", NS)
    assert pic is not None and pic.find(".//a:blip", NS).get(f"{{{NS['r']}}}embed")
    for om in gf.iter(f"{{{NS['m']}}}oMath"):
        assert _schema().validate(_strip_drawingml(om)), _schema().error_log


def test_edge_tex_error_becomes_a_reported_picture(edge):
    _, _, report, xml = edge
    bad = {f["tex"]: f["error"] for f in report.equations_as_picture if "foo" in (f["tex"] or "")}
    # an undefined macro, also inside a red region (where MathJax drops the red mathcolor)
    assert set(bad) == {"\\foo{x}", "\\textcolor{red}{\\foo}"}, bad
    assert all("undefined TeX macro" in e for e in bad.values())
    assert any("broken formula" in f["text"] for f in report.frames_as_picture)
    assert any("Red region" in f["text"] for f in report.frames_as_picture)
    assert "\\foo" not in "".join(t.text or "" for t in xml.iter(f"{{{NS['m']}}}t"))


def test_edge_graphics_and_mixed_content_are_pictures_with_warnings(edge):
    _, _, report, _ = edge
    reasons = [f["text"] for f in report.frames_as_picture if "mixed" in f["reason"]]
    assert any("inline icon" in t for t in reasons)           # <p> with an inline <svg>
    assert any("Loose text" in t for t in reasons)            # text next to a block child
    assert len(reasons) == 2                                  # and nothing else is "mixed"
    assert sum("exported as a picture" in w for w in report.warnings) == 4   # + icon list, svg table
    # block <svg> figure, gradient background, the two mixed blocks, the TeX-error paragraph
    assert report.pictures >= 5


def test_edge_ordered_list_and_line_break(edge):
    _, _, _, xml = edge
    sps = _sps(xml)
    ol = next(s for s in sps if [_norm(p) for p in s["paras"]] == ["First step.", "Second step."])
    for p in ol["el"].findall(".//a:p", NS):
        assert p.find("a:pPr/a:buAutoNum", NS) is not None
    para = next(s for s in sps if _norm(s["text"]).startswith("Line one"))
    assert para["el"].find(".//a:br", NS) is not None


def test_edge_edge_slide_is_schema_valid_math(edge):
    _, _, _, xml = edge
    for om in _omml_roots(xml):
        assert _schema().validate(_strip_drawingml(om)), _schema().error_log


def test_edge_table_formula_failure_turns_the_table_into_a_reported_picture(tmp_path):
    import aij_edge_poster
    import export_pptx

    real = export_pptx._default_mathml_to_omml

    def fail_on_pm(mml):
        if "&#xB1;" in mml or "±" in mml:
            raise ValueError("forced failure")
        return real(mml)

    html = aij_edge_poster.build(tmp_path / "e")
    out = tmp_path / "e.pptx"
    report = export_pptx.export(html, out, mathml_to_omml=fail_on_pm)
    assert report.tables == 0
    table_entries = [f for f in report.equations_as_picture if "table" in f["error"] or "forced" in f["error"]]
    assert {f["tex"] for f in table_entries} >= {"\\alpha", "0.1", "91.2 \\pm 0.3"}
    assert any("table" in f["reason"] for f in report.frames_as_picture)
    n = _math_count(html)
    assert report.equations_native + report.equations_inline_native + len(report.equations_as_picture) == n
    with zipfile.ZipFile(out) as z:
        xml = etree.fromstring(z.read("ppt/slides/slide1.xml"))
    assert not [gf for gf in xml.iter(f"{{{NS['p']}}}graphicFrame") if gf.find(".//a:tbl", NS) is not None]


def _edge_rect(html: Path, selector: str) -> tuple[float, float, float, float]:
    """Border box of `selector` in mm, relative to the poster (print render)."""
    from _posterly import canvas as _canvas, render as _r
    from playwright.sync_api import sync_playwright

    _, viewport = _canvas.resolve_canvas(html, None, label="[test]")
    with sync_playwright() as p:
        browser, _ctx, page = _r.open_print_emulated_page(p, viewport)
        try:
            page.goto(html.as_uri())
            page.wait_for_load_state("networkidle")
            _r.settle_page(page)
            r = page.evaluate("(sel) => { const P = document.querySelector('.poster').getBoundingClientRect();"
                              " const b = document.querySelector(sel).getBoundingClientRect();"
                              " return [b.x - P.x, b.y - P.y, b.width, b.height]; }", selector)
        finally:
            browser.close()
    return tuple(v / PX_PER_MM for v in r)


def test_edge_background_picture_carries_no_text(edge):
    """A CSS gradient behind text is a picture of the gradient ONLY; the text
    stays one native frame (no doubled 'ghost' text in the background)."""
    import io

    from PIL import Image

    html, out, report, xml = edge
    assert not [w for w in report.warnings if "background" in w and "not found" in w]
    assert any(_norm(s["text"]) == "GHOSTTEXT callout on a gradient" for s in _sps(xml))
    x, y, w, h = _edge_rect(html, "#grad-text")
    prs = pptx.Presentation(str(out))
    pics = [s for s in prs.slides[0].shapes if s.shape_type == 13
            and abs(s.left / EMU_PER_MM - x) <= TOL_MM and abs(s.top / EMU_PER_MM - y) <= TOL_MM
            and abs(s.width / EMU_PER_MM - w) <= TOL_MM]
    assert len(pics) == 1, "the gradient behind the text should be exactly one picture"
    im = Image.open(io.BytesIO(pics[0].image.blob)).convert("L")
    assert im.getextrema()[0] > 150, "dark (text) pixels in the background-only picture"


def test_edge_list_with_a_graphic_item_is_one_picture_with_markers(edge):
    _, _, report, xml = edge
    texts = " ".join(s["text"] for s in _sps(xml))
    assert "BULLETA" not in texts and "BULLETC" not in texts   # not split into marker-less frames
    lists = [f for f in report.frames_as_picture if f["reason"].startswith("list with")]
    assert len(lists) == 1 and "BULLETA" in lists[0]["text"]
    assert any(w.startswith("list with") for w in report.warnings)


def test_edge_table_with_a_graphic_cell_is_one_picture_without_leaked_text(edge):
    _, _, report, xml = edge
    all_text = "".join(t.text or "" for t in xml.iter(f"{{{NS['a']}}}t"))
    assert "checkmark" not in all_text and "SVGCELL" not in all_text
    assert [f for f in report.frames_as_picture if f["reason"].startswith("table with")]


def test_edge_inline_and_contents_wrappers_stay_native(edge):
    """<a><div>…</div></a> and a display:contents wrapper are walked as
    containers — their blocks are native text, the section is not a picture."""
    _, _, report, xml = edge
    texts = {_norm(s["text"]) for s in _sps(xml)}
    assert {"LINKCAPTION inside a link", "CONTENTSP1 first paragraph", "CONTENTSP2 second paragraph"} <= texts
    assert not [f for f in report.frames_as_picture if "Backgrounds, lists" in f["text"]]



def test_edge_image_css_effects_survive_in_the_picture(edge):
    """An image's CSS (here filter: brightness(0) invert(1) on a red data: URI
    with quotes in it) is part of what is on the sheet: the picture is white,
    not the source's red."""
    import io

    from PIL import Image

    html, out, _, _ = edge
    x, y, w, h = _edge_rect(html, "#fx-logo")
    prs = pptx.Presentation(str(out))
    pic = [s for s in prs.slides[0].shapes if s.shape_type == 13
           and abs(s.left / EMU_PER_MM - x) <= TOL_MM and abs(s.top / EMU_PER_MM - y) <= TOL_MM]
    assert len(pic) == 1
    im = Image.open(io.BytesIO(pic[0].image.blob)).convert("RGBA")
    r, g, b, a = im.getpixel((im.width // 2, im.height // 2))
    assert a > 200 and min(r, g, b) > 240, (r, g, b, a)



def test_single_lines_do_not_wrap_in_powerpoint(slide_xml):
    """Designer review: '№TODO' broke onto two lines in PowerPoint. Text that is
    one line in the HTML is exported with wrap="none"; multi-line text wraps."""
    frames = {_norm(s["text"]): s["el"].find("p:txBody/a:bodyPr", NS).get("wrap") for s in _sps(slide_xml)}
    assert frames["№1"] == "none"
    assert frames["1 Method"] == "none"
    title = "Progressive Cramming: Reliable Token Compression and What It Reveals"
    assert frames[title] == "square"                 # two lines in the HTML


def test_heading_runs_are_black(slide_xml):
    headings = [s for s in _sps(slide_xml)
                if any(r.get("sz") == "1400" for r in s["el"].iter(f"{{{NS['a']}}}rPr"))]
    assert len(headings) == 6
    for s in headings:
        colours = {c.get("val") for c in s["el"].iter(f"{{{NS['a']}}}srgbClr")}
        assert colours == {"000000"}, (s["text"], colours)



def test_export_preserves_guides_and_content_shape_bounds(exported):
    out, _ = exported
    with zipfile.ZipFile(out) as z, zipfile.ZipFile(SKILL / 'aij/assets/aij_template.pptx') as original:
        for name in ('ppt/viewProps.xml', 'ppt/presentation.xml'):
            def guides(data):
                root = etree.fromstring(data)
                return [dict(e.attrib) for e in root.iter() if etree.QName(e).localname == 'guide']
            assert guides(z.read(name)) == guides(original.read(name))
    prs = pptx.Presentation(str(out))
    # y between header and footer identifies content, including native tables.
    for shape in prs.slides[0].shapes:
        y = shape.top / EMU_PER_MM
        if 35 < y < 250:
            x, w, h = (v / EMU_PER_MM for v in (shape.left, shape.width, shape.height))
            assert x >= 13.229167 - .02 and x+w <= 177.270833 + .02, shape.name
            assert y >= 39.599306 - .02 and y+h <= 247.605903 + .02, shape.name
