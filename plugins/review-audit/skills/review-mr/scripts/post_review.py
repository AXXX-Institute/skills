#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "python-dotenv"]
# ///
"""Post an automated review to the current branch's GitLab MR.

Review publishing helper for /review-mr:

  # free-form markdown summary note (body from --body, --body-file, or stdin)
  uv run <review-audit-plugin>/skills/review-mr/scripts/post_review.py --summary --body-file summary.md

  # one inline discussion at FILE:LINE
  uv run <review-audit-plugin>/skills/review-mr/scripts/post_review.py --inline --file src/x.py --line 42 --severity CRITICAL --body "..."

  # many inline discussions from a JSON list (CRITICAL issues only; warnings and
  # suggestions belong in the summary note)
  #   [{"file": "src/x.py", "line": 42, "severity": "CRITICAL", "message": "..."}]
  uv run <review-audit-plugin>/skills/review-mr/scripts/post_review.py --inline-json comments.json

JSON result to stdout; diagnostics to stderr.
Requires GITLAB_TOKEN or MR_AUTO_REVIEW_GITLAB_TOKEN env var.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

from dotenv import load_dotenv

# Import the library shared by the plugin's skills.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "shared"))

load_dotenv()

from gitlab_ops import (  # noqa: E402
    collect_changed_lines,
    fetch_diff_versions,
    fetch_mr_changes,
    find_mr,
    format_inline_body,
    format_summary_body,
    gitlab_error,
    log,
    post_inline_discussion,
    post_note,
    resolve_project,
    summarize_inline_results,
)


def _head_sha() -> str:
    sha = os.getenv("CI_COMMIT_SHA", "").strip()
    if sha:
        return sha
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def _read_body(args: argparse.Namespace) -> str:
    if args.body is not None:
        return args.body
    if args.body_file:
        return pathlib.Path(args.body_file).read_text()
    return sys.stdin.read()


def post_summary(base_url: str, project_id: str, mr_iid: int, body: str) -> dict:
    full = format_summary_body(_head_sha(), body)
    post_note(base_url, project_id, mr_iid, full)
    return {"status": "ok", "posted": "summary"}


def _post_one_inline(
    base_url: str,
    project_id: str,
    mr_iid: int,
    item: dict,
    changed_lines: dict[str, set[int]],
    shas: dict,
) -> dict:
    file_path = item.get("file", "")
    requested = item.get("line")
    severity = item.get("severity", "")
    body = item.get("body") or item.get("message", "")

    if not file_path or not requested:
        return {
            "file": file_path,
            "line": requested,
            "status": "skipped",
            "reason": "missing file/line",
        }

    line = int(requested)
    valid = changed_lines.get(file_path, set())
    if line not in valid:
        nearby = [n for n in valid if abs(n - line) <= 3]
        if nearby:
            line = min(nearby, key=lambda n: abs(n - int(requested)))
        else:
            return {
                "file": file_path,
                "line": requested,
                "status": "skipped",
                "reason": "line not in diff",
            }

    full_body = format_inline_body(severity, body)
    try:
        post_inline_discussion(
            base_url, project_id, mr_iid, file_path, line, full_body, shas
        )
        log(f"  Posted inline: {file_path}:{line} [{severity}]")
        return {
            "file": file_path,
            "line": line,
            "severity": severity,
            "status": "posted",
        }
    except Exception as exc:  # noqa: BLE001 — report, keep posting the rest
        log(f"  WARNING: inline failed for {file_path}:{line}: {exc}")
        return {"file": file_path, "line": line, "status": "error", "reason": str(exc)}


def post_inline(base_url: str, project_id: str, mr_iid: int, items: list[dict]) -> dict:
    shas = fetch_diff_versions(base_url, project_id, mr_iid)
    if not shas:
        gitlab_error("Could not fetch diff versions; cannot post inline comments.")
    changes = fetch_mr_changes(base_url, project_id, mr_iid)
    changed_lines = collect_changed_lines(changes)
    results = [
        _post_one_inline(base_url, project_id, mr_iid, item, changed_lines, shas)
        for item in items
    ]
    return summarize_inline_results(results)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--summary", action="store_true", help="Post a free-form markdown summary note."
    )
    mode.add_argument(
        "--inline",
        action="store_true",
        help="Post one inline discussion (use --file/--line/--body).",
    )
    mode.add_argument(
        "--inline-json",
        metavar="FILE",
        help="Post inline discussions from a JSON list file.",
    )
    parser.add_argument("--body", help="Body text (summary or single inline).")
    parser.add_argument("--body-file", help="Read body from this file.")
    parser.add_argument("--file", help="File path for --inline.")
    parser.add_argument("--line", type=int, help="New-side line number for --inline.")
    parser.add_argument(
        "--severity", default="", help="CRITICAL/WARNING/SUGGESTION for --inline."
    )
    args = parser.parse_args()

    base_url, project_id, branch = resolve_project()
    mr = find_mr(base_url, project_id, branch)
    if not mr:
        gitlab_error(f"No open MR found for branch '{branch}'.")
    mr_iid = mr["iid"]
    log(f"  MR !{mr_iid}: {mr.get('title', '')}")

    if args.summary:
        output = post_summary(base_url, project_id, mr_iid, _read_body(args))
    elif args.inline_json:
        items = json.loads(pathlib.Path(args.inline_json).read_text())
        output = post_inline(base_url, project_id, mr_iid, items)
    else:  # --inline
        item = {
            "file": args.file,
            "line": args.line,
            "severity": args.severity,
            "body": _read_body(args),
        }
        output = post_inline(base_url, project_id, mr_iid, [item])

    json.dump(output, sys.stdout, indent=2)
    print()
    if output.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
