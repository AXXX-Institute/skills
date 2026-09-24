#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "python-dotenv"]
# ///
"""Delete the review bot's prior notes on the current branch's MR.

Phase 1 of /review-mr: wipes the slate so only the new review's notes remain.
Deletes the bot's own notes — both the summary comment(s) and inline diff
discussions — identified by author (the authenticated token user), leaving
human notes untouched. Iterating discussions covers every note type (inline
threads and standalone summary comments).

Outputs JSON to stdout. Diagnostics go to stderr.
Run with: uv run <gitlab-ai-plugin>/skills/review-mr/scripts/delete_prior_notes.py
Requires GITLAB_TOKEN or MR_AUTO_REVIEW_GITLAB_TOKEN env var.
"""

from __future__ import annotations

import json
import pathlib
import sys

from dotenv import load_dotenv

# Import the library shared by the plugin's skills.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "shared"))

load_dotenv()

from gitlab_ops import (  # noqa: E402
    delete_discussion_note,
    fetch_mr_discussions,
    find_mr,
    gitlab_error,
    gitlab_get_self,
    iter_review_notes,
    log,
    resolve_project,
    summarize_cleanup_result,
)


def main() -> None:
    base_url, project_id, branch = resolve_project()

    mr = find_mr(base_url, project_id, branch)
    if not mr:
        gitlab_error(f"No open MR found for branch '{branch}'.")
    mr_iid = mr["iid"]
    log(f"  MR !{mr_iid}: {mr.get('title', '')}")

    me = gitlab_get_self(base_url)
    my_id = me.get("id")
    log(f"  Authenticated as {me.get('username', '?')} (id {my_id})")

    discussions = fetch_mr_discussions(base_url, project_id, mr_iid)
    deleted: list[int] = []
    failed: list[dict] = []

    for discussion_id, note_id in iter_review_notes(discussions, my_id):
        try:
            delete_discussion_note(
                base_url, project_id, mr_iid, discussion_id, note_id
            )
            deleted.append(note_id)
            log(f"  Deleted note {note_id}")
        except Exception as exc:  # noqa: BLE001 — report, keep going
            failed.append({"id": note_id, "error": str(exc)})
            log(f"  WARNING: failed to delete {note_id}: {exc}")

    output = summarize_cleanup_result(mr_iid, deleted, failed)
    json.dump(output, sys.stdout, indent=2)
    print()
    if output["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
