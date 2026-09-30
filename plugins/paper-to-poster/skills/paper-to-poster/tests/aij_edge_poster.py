"""Build an AIJ poster that exercises the PPTX exporter's edge cases.

Used by tests/test_aij_export_pptx.py: the scaffold's frame and styles with a
content area holding everything the gallery example does not — formulas in
table cells, a TeX error, block and inline <svg>, an ordered list, <br>, a CSS
gradient background, and text mixed with block content.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

EDGE_BODY = r"""
  <div class="body-grid" data-measure-role="body">
    <div class="column" data-measure-role="column">
      <div class="section" data-measure-role="card">
        <div class="section-title"><span class="num">1</span>&ensp;Math in tables</div>
        <table class="result-table" id="math-table">
          <thead><tr><th class="method">Model</th><th>$\alpha$</th><th>Score</th></tr></thead>
          <tbody>
            <tr><td class="method">Ours</td><td>$0.1$</td><td class="best">$91.2 \pm 0.3$</td></tr>
            <tr><td class="method">Base</td><td colspan="2">n/a</td></tr>
          </tbody>
        </table>
        <p>Line one<br>line two after a break.</p>
        <ol>
          <li>First step.</li>
          <li>Second step.</li>
        </ol>
      </div>
      <div class="section" data-measure-role="card">
        <div class="section-title"><span class="num">2</span>&ensp;Graphics</div>
        <div class="figure" id="svg-figure">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 40" width="200" height="80">
            <rect width="100" height="40" fill="#26359A"/><text x="10" y="25" fill="#fff">SVG</text>
          </svg>
        </div>
        <p id="icon-para">Text with an inline icon <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" width="10" height="10"><circle cx="5" cy="5" r="5" fill="#1E9E53"/></svg> in the middle.</p>
        <div id="gradient-box" style="height: 20px; background-image: linear-gradient(90deg, #26359A, #43D374);"></div>
      </div>
    </div>
    <div class="column" data-measure-role="column">
      <div class="section" data-measure-role="card">
        <div class="section-title"><span class="num">3</span>&ensp;Errors and mixed content</div>
        <p id="tex-error">A broken formula $\foo{x}$ in text.</p>
        <div id="mixed">Loose text next to a block <div>block child</div></div>
        <p>A clean formula $x^2$ stays native.</p>
      </div>
    </div>
  </div>
"""


def build(dest: Path) -> Path:
    """Write the edge poster (+ frame assets) into `dest`; return its HTML path."""
    sys.path.insert(0, str(SKILL / "aij"))
    import prepare_assets

    dest.mkdir(parents=True, exist_ok=True)
    tpl = (SKILL / "templates" / "portrait_aij.html").read_text()
    start = tpl.index('  <div class="body-grid"')
    end = tpl.index("  <!-- =========================== FOOTER")
    html = tpl[:start] + EDGE_BODY + "\n" + tpl[end:]
    out = dest / "poster.html"
    out.write_text(html)
    prepare_assets.prepare(dest / "images")
    return out


if __name__ == "__main__":
    d = Path(sys.argv[1])
    if d.exists():
        shutil.rmtree(d)
    print(build(d))
