#!/usr/bin/env python3
"""Fast, dependency-free structural validation for the AXXX-Institute/skills
marketplace. Runs in CI (see .github/workflows/ci.yml) and locally:

    python3 .github/scripts/validate.py

It validates the marketplace/plugin/skill wiring WITHOUT installing anything,
launching Claude, or running skill evaluations. Exit code 0 = all good, 1 = at
least one error. Warnings never fail the build.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report any parse failure
        err(f"{path.relative_to(ROOT)}: invalid JSON — {exc}")
        return None


# --- YAML frontmatter (minimal, no PyYAML) --------------------------------
_KEY = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")


def parse_frontmatter(text: str) -> dict | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    data: dict[str, str] = {}
    key = None
    buf: list[str] = []

    def flush():
        nonlocal key, buf
        if key is not None:
            val = "\n".join(buf).strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[key] = val
        key, buf = None, []

    for ln in lines[1:end]:
        m = _KEY.match(ln)
        if m and not ln[:1].isspace():
            flush()
            key = m.group(1)
            inline = m.group(2).strip()
            buf = [] if inline in (">", ">-", ">+", "|", "|-", "|+") else [inline]
        elif key is not None:
            buf.append(ln.strip())
    flush()
    return data


MAX_DESC = 1024  # Claude Code skill `description` hard cap


def check_skill(skill_dir: Path, names_seen: dict[str, Path]) -> str | None:
    """Validate one skill directory; return its frontmatter name (or None)."""
    rel = skill_dir.relative_to(ROOT)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        err(f"{rel}: missing SKILL.md")
        return None
    fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm is None:
        err(f"{rel}/SKILL.md: missing or malformed YAML frontmatter (--- … ---)")
        return None
    name = fm.get("name", "").strip()
    desc = fm.get("description", "").strip()
    if not name:
        err(f"{rel}/SKILL.md: frontmatter has no `name`")
    elif name != skill_dir.name:
        err(f"{rel}/SKILL.md: frontmatter name '{name}' != directory '{skill_dir.name}'")
    if not desc:
        err(f"{rel}/SKILL.md: frontmatter has no `description`")
    elif len(desc) > MAX_DESC:
        err(f"{rel}/SKILL.md: description is {len(desc)} chars (> {MAX_DESC} cap)")
    if name:
        if name in names_seen:
            err(f"duplicate skill name '{name}': {rel} and {names_seen[name]}")
        names_seen[name] = rel
    # Light evals.json check (optional file)
    evals = skill_dir / "evals" / "evals.json"
    if evals.is_file():
        data = load_json(evals)
        if isinstance(data, dict):
            if data.get("skill_name") not in (None, name):
                warn(f"{rel}/evals/evals.json: skill_name '{data.get('skill_name')}' != '{name}'")
            if not isinstance(data.get("evals"), list):
                err(f"{rel}/evals/evals.json: `evals` must be a list")
    return name or None


def main() -> int:
    # 1. Root invariants: pure marketplace, new plugin layout.
    mkt_path = ROOT / ".claude-plugin" / "marketplace.json"
    if not mkt_path.is_file():
        err(".claude-plugin/marketplace.json is missing")
        return report()
    if (ROOT / ".claude-plugin" / "plugin.json").exists():
        err(".claude-plugin/plugin.json exists — root must be a pure marketplace "
            "(plugins live under plugins/<name>/, see ADR 0005)")
    if (ROOT / "skills").is_dir():
        err("top-level skills/ directory exists — skills now live under "
            "plugins/<name>/skills/ (see ADR 0005)")

    mkt = load_json(mkt_path)
    if mkt is None:
        return report()

    # 2. Marketplace-level fields.
    for field in ("name", "plugins"):
        if field not in mkt:
            err(f"marketplace.json: missing required field `{field}`")
    plugins = mkt.get("plugins") or []
    if not isinstance(plugins, list) or not plugins:
        err("marketplace.json: `plugins` must be a non-empty array")
        plugins = []

    # 3. Each plugin entry + its directory + manifest.
    seen_plugin_names: set[str] = set()
    skill_names: dict[str, Path] = {}
    all_skill_names: list[str] = []
    for i, entry in enumerate(plugins):
        pname = entry.get("name")
        src = entry.get("source")
        if not pname:
            err(f"marketplace.json: plugins[{i}] has no `name`")
        if not src:
            err(f"marketplace.json: plugin '{pname}' has no `source`")
            continue
        if pname in seen_plugin_names:
            err(f"marketplace.json: duplicate plugin name '{pname}'")
        seen_plugin_names.add(pname)
        if not (isinstance(src, str) and src.startswith("./")):
            err(f"marketplace.json: plugin '{pname}' source '{src}' must be a "
                "relative path starting with './'")
            continue
        pdir = (ROOT / src).resolve()
        if not pdir.is_dir():
            err(f"marketplace.json: plugin '{pname}' source '{src}' does not exist")
            continue
        manifest = pdir / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            err(f"{src}: missing .claude-plugin/plugin.json")
            continue
        pj = load_json(manifest)
        if isinstance(pj, dict):
            if pj.get("name") != pname:
                err(f"{src}/.claude-plugin/plugin.json name '{pj.get('name')}' "
                    f"!= marketplace entry '{pname}'")
            if pname != pdir.name:
                warn(f"plugin '{pname}' lives in directory '{pdir.name}' (name mismatch)")
        # 4. Skills under this plugin.
        skills_root = pdir / "skills"
        skill_dirs = sorted(p for p in skills_root.glob("*") if p.is_dir()) if skills_root.is_dir() else []
        if not skill_dirs:
            err(f"{src}: plugin ships no skills under skills/")
        for sd in skill_dirs:
            n = check_skill(sd, skill_names)
            if n:
                all_skill_names.append(n)

    # 5. Every *.json in the repo parses.
    for jp in ROOT.rglob("*.json"):
        if ".git" in jp.parts or "__pycache__" in jp.parts:
            continue
        load_json(jp)

    # 6. Internal markdown links resolve (marketplace-level docs only).
    doc_files = [ROOT / "README.md", ROOT / "CLAUDE.md", ROOT / "CONTEXT.md"]
    doc_files += sorted((ROOT / "docs").rglob("*.md")) if (ROOT / "docs").is_dir() else []
    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for md in doc_files:
        if not md.is_file():
            continue
        for target in link_re.findall(md.read_text(encoding="utf-8")):
            t = target.strip().split()[0]  # drop optional "title"
            t = t.split("#", 1)[0].split("?", 1)[0]
            if not t or t.startswith(("http://", "https://", "mailto:", "/", "#")):
                continue
            if not (t.endswith((".md", ".json", ".html", ".yml", ".yaml", ".py", ".txt")) or "/" in t):
                continue
            if not (md.parent / t).exists():
                err(f"{md.relative_to(ROOT)}: broken relative link -> {t}")

    # 7. Sync guard: every skill is listed in README and described on the Pages site.
    page_files = [
        ROOT / "site" / "index.html",
        ROOT / "site" / "mlspace-jobs.html",
        ROOT / "plugins/paper-to-poster/skills/paper-to-poster/examples/index.html",
    ]
    pages_txt = "\n".join(p.read_text(encoding="utf-8") for p in page_files if p.is_file())
    readme_txt = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
    for n in all_skill_names:
        if n not in readme_txt:
            err(f"skill '{n}' is not listed in README.md (Plugins & skills table)")
        if n not in pages_txt:
            err(f"skill '{n}' is not described on the GitHub Pages site "
                "(site/*.html or the paper-to-poster gallery)")

    # 8. Codex/Claude parity: same plugin set (dual manifests) and same skill set.
    check_codex_parity(all_skill_names)

    return report()


def check_codex_parity(claude_skill_names: list[str]) -> None:
    """Every Claude plugin has a matching Codex plugin manifest, and the Codex
    `.agents/skills/` view exposes exactly the same skills (resolving to the same
    files). Skips silently if no Codex mirror exists yet."""
    agents_skills = ROOT / ".agents" / "skills"
    codex_manifests = sorted(ROOT.glob("plugins/*/.codex-plugin/plugin.json"))
    if not agents_skills.exists() and not codex_manifests:
        return  # no Codex mirror in this repo — nothing to check
    # Plugin-level parity: each plugins/<p> with a Claude manifest must have a Codex one, same name.
    for claude_mf in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
        pdir = claude_mf.parent.parent
        codex_mf = pdir / ".codex-plugin" / "plugin.json"
        if not codex_mf.is_file():
            err(f"{pdir.relative_to(ROOT)}: has .claude-plugin/plugin.json but no "
                ".codex-plugin/plugin.json (Codex/Claude plugin lists must match)")
            continue
        cj, xj = load_json(claude_mf), load_json(codex_mf)
        if isinstance(cj, dict) and isinstance(xj, dict) and cj.get("name") != xj.get("name"):
            err(f"{pdir.relative_to(ROOT)}: plugin name differs between "
                f"Claude ('{cj.get('name')}') and Codex ('{xj.get('name')}')")
    # Marketplace-level parity: the two catalogs list the same plugin names.
    claude_mkt = load_json(ROOT / ".claude-plugin" / "marketplace.json") or {}
    codex_mkt = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    if codex_mkt is None:
        err(".agents/plugins/marketplace.json is missing (Codex marketplace mirror)")
    else:
        cnames = {p.get("name") for p in claude_mkt.get("plugins", [])}
        xnames = {p.get("name") for p in codex_mkt.get("plugins", [])}
        if cnames != xnames:
            err(f"marketplace plugin lists differ — Claude {sorted(cnames)} "
                f"vs Codex {sorted(xnames)}")

    # Skill-set parity: .agents/skills/<name> resolves to the same SKILL.md set.
    codex_skill_names = []
    if agents_skills.is_dir():
        for sd in sorted(p for p in agents_skills.iterdir() if p.is_dir() or p.is_symlink()):
            sm = sd / "SKILL.md"
            if not sm.is_file():
                err(f".agents/skills/{sd.name}: no SKILL.md (broken symlink?)")
                continue
            codex_skill_names.append(sd.name)
    missing = sorted(set(claude_skill_names) - set(codex_skill_names))
    extra = sorted(set(codex_skill_names) - set(claude_skill_names))
    if missing:
        err(f"Codex .agents/skills/ is missing skills present for Claude: {missing}")
    if extra:
        err(f"Codex .agents/skills/ has skills not in the Claude plugins: {extra}")


def report() -> int:
    for w in warnings:
        print(f"::warning:: {w}" if _in_ci() else f"WARN  {w}")
    if errors:
        for e in errors:
            print(f"::error:: {e}" if _in_ci() else f"ERROR {e}")
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) — FAILED")
        return 1
    print(f"OK — marketplace, {len(_plugin_count())} plugin(s), all skills valid "
          f"({len(warnings)} warning(s))")
    return 0


def _in_ci() -> bool:
    import os
    return bool(os.environ.get("GITHUB_ACTIONS"))


def _plugin_count():
    mkt = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    return mkt.get("plugins", [])


if __name__ == "__main__":
    sys.exit(main())
