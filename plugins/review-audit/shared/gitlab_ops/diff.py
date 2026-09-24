"""MR diff filtering, prioritisation, and changed-line parsing."""

from __future__ import annotations

import os
import re

# Files to skip in diff (binary, generated, large)
SKIP_PATTERNS = {
    "uv.lock",
    "poetry.lock",
    "package-lock.json",
}
SKIP_EXTENSIONS = {
    ".parquet",
    ".bin",
    ".safetensors",
    ".ckpt",
    ".pt",
    ".pth",
    ".whl",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
}

# Priority order for diff inclusion (lower = higher priority)
EXTENSION_PRIORITY = {
    ".py": 0,
    ".yaml": 1,
    ".yml": 1,
    ".toml": 2,
    ".sh": 3,
    ".md": 4,
}

MAX_DIFF_CHARS = 300_000


def _should_skip_file(path: str) -> bool:
    basename = os.path.basename(path)
    if basename in SKIP_PATTERNS:
        return True
    _, ext = os.path.splitext(path)
    return ext.lower() in SKIP_EXTENSIONS


def _file_priority(path: str) -> int:
    _, ext = os.path.splitext(path)
    return EXTENSION_PRIORITY.get(ext.lower(), 10)


def build_diff(changes: list[dict]) -> str:
    """Build a unified diff string from GitLab MR changes, with filtering/truncation."""
    valid = []
    skipped = []
    for change in changes:
        path = change.get("new_path", change.get("old_path", ""))
        if change.get("deleted_file"):
            if _should_skip_file(path):
                skipped.append(path)
                continue
        elif _should_skip_file(path):
            skipped.append(path)
            continue
        diff_text = change.get("diff", "")
        if not diff_text:
            skipped.append(path)
            continue
        old_path = change.get("old_path", path)
        valid.append((old_path, path, diff_text))

    valid.sort(key=lambda x: _file_priority(x[1]))

    parts = []
    total_len = 0
    truncated_files = []
    for old_path, path, diff_text in valid:
        header = f"--- a/{old_path}\n+++ b/{path}\n"
        entry = header + diff_text + "\n"
        if total_len + len(entry) > MAX_DIFF_CHARS:
            truncated_files.append(path)
            continue
        parts.append(entry)
        total_len += len(entry)

    result = "".join(parts)
    omitted = skipped + truncated_files
    if omitted:
        result += f"\n[Omitted {len(omitted)} file(s): {', '.join(omitted[:10])}"
        if len(omitted) > 10:
            result += f" and {len(omitted) - 10} more"
        result += "]\n"
    return result


def collect_changed_lines(changes: list[dict]) -> dict[str, set[int]]:
    """Parse diff hunks to find which new-side line numbers exist in the diff."""
    file_lines: dict[str, set[int]] = {}
    for change in changes:
        path = change.get("new_path", "")
        diff_text = change.get("diff", "")
        if not path or not diff_text:
            continue
        lines_set: set[int] = set()
        current_line = 0
        for line in diff_text.splitlines():
            hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if hunk_match:
                current_line = int(hunk_match.group(1))
                continue
            if line.startswith("-"):
                continue
            if line.startswith("\\"):
                # Git hunk metadata (for example, "No newline at end of file")
                # is not a source line on either side.
                continue
            if line.startswith("+"):
                lines_set.add(current_line)
                current_line += 1
            else:
                current_line += 1
        if lines_set:
            file_lines[path] = lines_set
    return file_lines
