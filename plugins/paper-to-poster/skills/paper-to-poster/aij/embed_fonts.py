#!/usr/bin/env python3
"""Embed SB Sans Display and Text into an exported AIJ .pptx (docs/adr/0013).

PowerPoint only shows an SB Sans face on a machine that has it installed —
otherwise it silently substitutes (typically Calibri). The organisers' own
template avoids that by embedding its fonts; this does the same for the export:

  * the faces the poster's text actually uses (of Light 300 / Regular 400 /
    Semibold 600 / Bold 700 for Display; Regular 400 / Semibold 600 for Text) are downloaded at export time from the CDN URLs in
    aij/fonts.css (the same files the HTML renders with — nothing is read from,
    or written to, this repo);
  * they are named the way the organisers' desktop fonts are (one family per
    non-RIBBI weight, like the template's "SB Sans Display Semibold"):
    "SB Sans Display" Regular + Bold, "SB Sans Display Light" and
    "SB Sans Display Semibold", "SB Sans Text" and "SB Sans Text Semibold" — exactly the typefaces export_pptx.py writes on
    every text run;
  * each face is wrapped as an Embedded OpenType (EOT 2.2, uncompressed) part
    `ppt/fonts/fontN.fntdata` and listed in presentation.xml's
    <p:embeddedFontLst> with embedTrueTypeFonts="1" — the structure PowerPoint
    itself writes (the organisers' template was the reference).

The faces are installable-embedding fonts (OS/2 fsType 0). Renaming rewrites
only the naming records (nameIDs 1/2/4/6; 16/17 dropped) and the style bits
(OS/2 fsSelection, head.macStyle) of each embedded face; outlines and metrics are
untouched.
"""
from __future__ import annotations

import io
import re
import struct
import urllib.request
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS_CSS = HERE / "fonts.css"

FONT_RELTYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
FONT_CONTENT_TYPE = "application/x-fontdata"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

#: (CSS family, weight) -> (pptx typeface, style slot, EOT/ name-table subfamily)
FACES = {
    ("SB Sans Display", 300): ("SB Sans Display Light", "regular", "Regular"),
    ("SB Sans Display", 400): ("SB Sans Display", "regular", "Regular"),
    ("SB Sans Display", 600): ("SB Sans Display Semibold", "regular", "Regular"),
    ("SB Sans Display", 700): ("SB Sans Display", "bold", "Bold"),
    ("SB Sans Text", 400): ("SB Sans Text", "regular", "Regular"),
    ("SB Sans Text", 600): ("SB Sans Text Semibold", "regular", "Regular"),
}
#: (pptx typeface, style slot) -> (CSS family, weight)
SLOT_WEIGHT = {(face, slot): w for w, (face, slot, _sub) in FACES.items()}


@dataclass
class Face:
    typeface: str
    slot: str          # "regular" | "bold"
    ttf: bytes


def cdn_urls(css: str | None = None) -> dict[tuple[str, int], str]:
    """(family, weight) -> woff2 URL, from aij/fonts.css."""
    css = css if css is not None else FONTS_CSS.read_text()
    out = {}
    for block in re.findall(r"@font-face\s*{(.*?)}", css, re.DOTALL):
        url = re.search(r'url\("([^"]+)"\)', block)
        weight = re.search(r"font-weight:\s*(\d+)", block)
        family = re.search(r'font-family:\s*"([^"]+)"', block)
        if url and weight and family:
            out[(family.group(1), int(weight.group(1)))] = url.group(1)
    return out


def woff2_to_ttf(data: bytes) -> bytes:
    from fontTools.ttLib import TTFont

    font = TTFont(io.BytesIO(data))
    font.flavor = None
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def rename(ttf: bytes, family: str, subfamily: str) -> bytes:
    """Give a face the GDI-style names PowerPoint matches on: family
    (nameID 1/16 dropped), subfamily (2), full (4), PostScript (6); set the
    RIBBI style bits to match `subfamily`."""
    from fontTools.ttLib import TTFont

    font = TTFont(io.BytesIO(ttf))
    name = font["name"]
    full = family if subfamily == "Regular" else f"{family} {subfamily}"
    ps = re.sub(r"[^A-Za-z0-9-]", "", family.replace(" ", "")) + ("" if subfamily == "Regular" else f"-{subfamily}")
    for nid in (16, 17):
        name.removeNames(nameID=nid)
    for nid, value in ((1, family), (2, subfamily), (4, full), (6, ps)):
        name.removeNames(nameID=nid)
        name.setName(value, nid, 3, 1, 0x409)
        name.setName(value, nid, 1, 0, 0)
    os2, head = font["OS/2"], font["head"]
    bold = subfamily == "Bold"
    os2.fsSelection = (os2.fsSelection & ~0b1100001) | (0b100000 if bold else 0b1000000)
    head.macStyle = (head.macStyle & ~0b11) | (1 if bold else 0)
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def used_weights(slide_xml) -> list[tuple[str, int]]:
    """CSS (family, weight) pairs of the faces the slide's text runs use ((typeface, b) of
    every <a:rPr> with an SB Sans <a:latin>)."""
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    out = set()
    for rpr in slide_xml.iter(f"{{{a}}}rPr"):
        latin = rpr.find(f"{{{a}}}latin")
        if latin is None:
            continue
        slot = "bold" if rpr.get("b") in ("1", "true") else "regular"
        w = SLOT_WEIGHT.get((latin.get("typeface"), slot))
        if w is not None:
            out.add(w)
    return sorted(out)


def fetch_faces(weights: list[tuple[str, int]] | None = None, timeout: float = 20.0) -> list[Face]:
    """Download + convert + name the faces for `weights` (default: all supported faces);
    raises on any failure."""
    urls = cdn_urls()
    weights = sorted(FACES) if weights is None else weights
    missing = set(weights) - set(urls)
    if missing:
        raise ValueError(f"aij/fonts.css has no @font-face for weight(s) {sorted(missing)}")
    faces = []
    for weight in weights:
        typeface, slot, sub = FACES[weight]
        with urllib.request.urlopen(urls[weight], timeout=timeout) as r:
            ttf = woff2_to_ttf(r.read())
        faces.append(Face(typeface, slot, rename(ttf, typeface, sub)))
    return faces


def _utf16(s: str) -> bytes:
    return s.encode("utf-16-le")


def ttf_to_eot(ttf: bytes) -> bytes:
    """Wrap a TrueType font as an uncompressed EOT 2.2 (the container PowerPoint
    uses for .fntdata), with the header fields PowerPoint writes."""
    from fontTools.ttLib import TTFont

    font = TTFont(io.BytesIO(ttf))
    os2, head, name = font["OS/2"], font["head"], font["name"]
    p = os2.panose
    panose = bytes([p.bFamilyType, p.bSerifStyle, p.bWeight, p.bProportion, p.bContrast,
                    p.bStrokeVariation, p.bArmStyle, p.bLetterForm, p.bMidline, p.bXHeight])
    family = name.getDebugName(1) or ""
    style = name.getDebugName(2) or "Regular"
    version = name.getDebugName(5) or ""
    full = name.getDebugName(4) or family
    body = bytearray()
    body += panose
    body += struct.pack("<BB", 1, 1 if os2.fsSelection & 1 else 0)          # DEFAULT_CHARSET, Italic
    body += struct.pack("<IHH", os2.usWeightClass, os2.fsType, 0x504C)
    body += struct.pack("<IIII", os2.ulUnicodeRange1, os2.ulUnicodeRange2, os2.ulUnicodeRange3, os2.ulUnicodeRange4)
    body += struct.pack("<II", getattr(os2, "ulCodePageRange1", 0), getattr(os2, "ulCodePageRange2", 0))
    body += struct.pack("<I", head.checkSumAdjustment)
    body += struct.pack("<IIII", 0, 0, 0, 0)                                  # Reserved1-4
    body += struct.pack("<H", 0)                                              # Padding1
    # names as PowerPoint writes them: family/style NUL-terminated, version/full not
    for s in (family + "\0", style + "\0", version, full):
        b = _utf16(s)
        body += struct.pack("<H", len(b)) + b + struct.pack("<H", 0)
    body += struct.pack("<H", 0)                                              # RootStringSize (no root string)
    body += struct.pack("<IIHH", 0x50475342, 0, 0, 0)                         # RootStringCheckSum, EUDCCodePage, Padding6, SignatureSize
    body += struct.pack("<II", 0, 0)                                          # EUDCFlags, EUDCFontSize
    header_len = 4 * 4 + len(body)
    eot = struct.pack("<IIII", header_len + len(ttf), len(ttf), 0x00020002, 0) + bytes(body) + ttf
    return eot


def parse_eot(eot: bytes) -> dict:
    """Read back an EOT header (used by the tests)."""
    size, data_size, version, flags = struct.unpack_from("<IIII", eot, 0)
    o = 16 + 10 + 2
    weight, fs_type, magic = struct.unpack_from("<IHH", eot, o)
    o += 8 + 16 + 8 + 4 + 16 + 2
    names = []
    for _ in range(4):
        (n,) = struct.unpack_from("<H", eot, o)
        names.append(eot[o + 2:o + 2 + n].decode("utf-16-le").rstrip("\0"))
        o += 2 + n + 2
    (root,) = struct.unpack_from("<H", eot, o)
    o += 2 + root + 4 + 4 + 2
    (sig,) = struct.unpack_from("<H", eot, o)
    o += 2 + sig + 4
    (eudc,) = struct.unpack_from("<I", eot, o)
    o += 4 + eudc
    return {"size": size, "data_size": data_size, "version": version, "flags": flags, "weight": weight,
            "fsType": fs_type, "magic": magic, "family": names[0], "style": names[1], "full": names[3],
            "font_data": eot[o:o + data_size], "header_len": o}


def embed(prs, faces: list[Face]) -> list[str]:
    """Add `faces` to a python-pptx Presentation as embedded fonts; return the
    typefaces embedded."""
    from lxml import etree
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI

    pres_part = prs.part
    root = pres_part._element
    p = lambda t: f"{{{P_NS}}}{t}"  # noqa: E731
    old = root.find(p("embeddedFontLst"))
    if old is not None:
        root.remove(old)
    lst = etree.Element(p("embeddedFontLst"))
    by_face: dict[str, etree._Element] = {}
    for i, face in enumerate(faces, start=1):
        part = Part(PackURI(f"/ppt/fonts/font{i}.fntdata"), FONT_CONTENT_TYPE, pres_part.package, ttf_to_eot(face.ttf))
        rid = pres_part.relate_to(part, FONT_RELTYPE)
        ef = by_face.get(face.typeface)
        if ef is None:
            ef = etree.SubElement(lst, p("embeddedFont"))
            etree.SubElement(ef, p("font"), typeface=face.typeface, pitchFamily="34", charset="0")
            by_face[face.typeface] = ef
        etree.SubElement(ef, p(face.slot), {f"{{{R_NS}}}id": rid})
    for ef in lst:   # CT_EmbeddedFontListEntry: font, regular, bold, italic, boldItalic
        order = {p("font"): 0, p("regular"): 1, p("bold"): 2, p("italic"): 3, p("boldItalic"): 4}
        ef[:] = sorted(ef, key=lambda e: order[e.tag])
    # CT_Presentation: … sldSz, notesSz, smartTags?, embeddedFontLst?, custShowLst? …
    anchor = root.find(p("smartTags"))
    if anchor is None:
        anchor = root.find(p("notesSz"))
    anchor.addnext(lst)
    root.set("embedTrueTypeFonts", "1")
    return list(by_face)
