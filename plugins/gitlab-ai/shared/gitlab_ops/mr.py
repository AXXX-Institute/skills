"""Merge request lookup and note/discussion read+write helpers."""

from __future__ import annotations

import urllib.parse

from .api import gitlab_delete, gitlab_get, gitlab_post, gitlab_put


def find_mr(base_url: str, project_id: str, branch: str) -> dict | None:
    encoded_branch = urllib.parse.quote(branch, safe="/")
    mrs = gitlab_get(
        base_url,
        project_id,
        f"merge_requests?source_branch={encoded_branch}&state=opened",
    )
    return mrs[0] if mrs else None


def fetch_mr_changes(base_url: str, project_id: str, mr_iid: int) -> list[dict]:
    """Return the per-file change list for an MR."""
    payload = gitlab_get(base_url, project_id, f"merge_requests/{mr_iid}/changes")
    if payload and isinstance(payload[0], dict):
        return payload[0].get("changes", [])
    return []


def fetch_mr_discussions(base_url: str, project_id: str, mr_iid: int) -> list[dict]:
    """Fetch all discussion threads on the MR."""
    return gitlab_get(base_url, project_id, f"merge_requests/{mr_iid}/discussions")


def fetch_diff_versions(base_url: str, project_id: str, mr_iid: int) -> dict | None:
    """Fetch the latest diff-version SHAs needed to position inline comments."""
    versions = gitlab_get(base_url, project_id, f"merge_requests/{mr_iid}/versions")
    if not versions:
        return None
    latest = versions[0]
    return {
        "base_sha": latest.get("base_commit_sha"),
        "head_sha": latest.get("head_commit_sha"),
        "start_sha": latest.get("start_commit_sha"),
    }


def post_note(base_url: str, project_id: str, mr_iid: int, body: str) -> None:
    """Post a plain (non-positioned) note to the MR."""
    gitlab_post(base_url, project_id, f"merge_requests/{mr_iid}/notes", {"body": body})


def post_inline_discussion(
    base_url: str,
    project_id: str,
    mr_iid: int,
    file_path: str,
    line: int,
    body: str,
    shas: dict,
) -> None:
    """Open an inline discussion anchored to ``file_path``:``line`` (new side)."""
    gitlab_post(
        base_url,
        project_id,
        f"merge_requests/{mr_iid}/discussions",
        {
            "body": body,
            "position": {
                "position_type": "text",
                "new_path": file_path,
                "new_line": line,
                "base_sha": shas["base_sha"],
                "head_sha": shas["head_sha"],
                "start_sha": shas["start_sha"],
            },
        },
    )


def resolve_discussion(
    base_url: str, project_id: str, mr_iid: int, discussion_id: str
) -> None:
    """Mark a discussion thread as resolved."""
    gitlab_put(
        base_url,
        project_id,
        f"merge_requests/{mr_iid}/discussions/{discussion_id}",
        {"resolved": True},
    )


def delete_discussion_note(
    base_url: str, project_id: str, mr_iid: int, discussion_id: str, note_id: int
) -> None:
    """Delete one note from an MR discussion.

    Works for every note type — inline diff threads and standalone summary
    comments both surface as discussions with notes.
    """
    gitlab_delete(
        base_url,
        project_id,
        f"merge_requests/{mr_iid}/discussions/{discussion_id}/notes/{note_id}",
    )
