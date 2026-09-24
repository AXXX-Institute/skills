#!/usr/bin/env python3
"""Generate one dependency-free GitHub Pages route for every marketplace skill."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_URL = "https://github.com/AXXX-Institute/skills"


@dataclass(frozen=True)
class SkillPage:
    name: str
    description: str
    plugin: str
    license: str
    explicit_only: bool
    relative_dir: Path
    skill_source: str

    @property
    def claude_invocation(self) -> str:
        return f"/{self.name}" if self.name == self.plugin else f"/{self.plugin}:{self.name}"

    @property
    def codex_invocation(self) -> str:
        return f"${self.name}" if self.name == self.plugin else f"${self.plugin}:{self.name}"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("unterminated YAML frontmatter") from exc

    fields: dict[str, str] = {}
    key: str | None = None
    values: list[str] = []

    def flush() -> None:
        nonlocal key, values
        if key is not None:
            fields[key] = " ".join(value.strip() for value in values).strip().strip("\"'")
        key, values = None, []

    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):(.*)$", line)
        if match and not line[:1].isspace():
            flush()
            key = match.group(1)
            value = match.group(2).strip()
            values = [] if value in {">", ">-", "|", "|-"} else [value]
        elif key is not None:
            values.append(line)
    flush()
    return fields, "\n".join(lines[end + 1 :]).strip()


def discover_skills() -> list[SkillPage]:
    marketplace = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    skills: list[SkillPage] = []
    for entry in marketplace["plugins"]:
        plugin = entry["name"]
        plugin_dir = ROOT / entry["source"]
        manifest = json.loads(
            (plugin_dir / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        license_name = manifest.get("license", "See plugin license")
        for skill_dir in sorted((plugin_dir / "skills").iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_md.is_file():
                continue
            source = skill_md.read_text(encoding="utf-8")
            fields, _ = parse_frontmatter(source)
            openai_metadata = skill_dir / "agents" / "openai.yaml"
            explicit_only = fields.get("disable-model-invocation", "").lower() == "true"
            if openai_metadata.is_file():
                explicit_only = explicit_only or bool(
                    re.search(
                        r"^\s*allow_implicit_invocation:\s*false\s*$",
                        openai_metadata.read_text(encoding="utf-8"),
                        re.MULTILINE,
                    )
                )
            skills.append(
                SkillPage(
                    name=fields["name"],
                    description=fields["description"],
                    plugin=plugin,
                    license=license_name,
                    explicit_only=explicit_only,
                    relative_dir=skill_dir.relative_to(ROOT),
                    skill_source=source,
                )
            )
    return sorted(skills, key=lambda skill: skill.name)


def render_page(skill: SkillPage, all_skills: list[SkillPage]) -> str:
    esc = html.escape
    mode = "Explicit invocation only" if skill.explicit_only else "Automatic discovery or direct invocation"
    source_url = f"{REPOSITORY_URL}/tree/main/{skill.relative_dir.as_posix()}"
    skill_url = f"{REPOSITORY_URL}/blob/main/{skill.relative_dir.as_posix()}/SKILL.md"
    plugin_pages = {
        "gitlab-ai": "../gitlab-ai.html",
        "mlspace-jobs": "../mlspace-jobs.html",
    }
    related_links = ""
    if skill.plugin in plugin_pages:
        related_links += (
            f'<a href="{plugin_pages[skill.plugin]}">Open {esc(skill.plugin)} overview →</a>'
        )
    if skill.name == "paper-to-poster":
        related_links += '<a href="gallery.html">Open poster gallery →</a>'
    navigation = "".join(
        f'<a href="../{esc(item.name)}/">{esc(item.name)}</a>' for item in all_skills
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(skill.name)} — AXXX skills</title>
<link rel="stylesheet" href="../assets/styles.css">
</head>
<body class="page-skill"><div class="bar"></div><main>
  <p class="breadcrumb"><a href="../">← All AXXX skills</a></p>
  <h1>{esc(skill.name)}</h1>
  <p class="sub">{esc(skill.description)}</p>
  <div class="skill-meta">
    <div class="card"><div class="label">Plugin</div><strong>{esc(skill.plugin)}</strong></div>
    <div class="card"><div class="label">License</div><strong>{esc(skill.license)}</strong></div>
    <div class="card"><div class="label">Invocation</div><strong>{esc(mode)}</strong></div>
  </div>
  <h2>Install</h2>
  <div class="skill-grid">
    <section class="card install-card"><h3>Claude Code</h3><pre><code>/plugin marketplace add AXXX-Institute/skills
/plugin install {esc(skill.plugin)}@axxx-institute</code></pre><p>Run <code>{esc(skill.claude_invocation)}</code>.</p></section>
    <section class="card install-card"><h3>OpenAI Codex</h3><pre><code>codex plugin marketplace add AXXX-Institute/skills
codex plugin add {esc(skill.plugin)}@axxx-institute</code></pre><p>Run <code>{esc(skill.codex_invocation)}</code>.</p></section>
  </div>
  <div class="actions"><a href="{esc(source_url)}">README and source on GitHub →</a><a href="{esc(skill_url)}">Open SKILL.md →</a>{related_links}</div>
  <details><summary>View complete skill instructions</summary><pre><code>{esc(skill.skill_source)}</code></pre></details>
  <h2>Other skills</h2><nav class="skill-nav">{navigation}</nav>
</main><script src="../assets/site.js"></script></body>
</html>
"""


def build_pages(output: Path) -> list[Path]:
    skills = discover_skills()
    written: list[Path] = []
    for skill in skills:
        page = output / skill.name / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(render_page(skill, skills), encoding="utf-8")
        written.append(page)
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    written = build_pages(args.output)
    print(f"Generated {len(written)} skill page(s) in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
