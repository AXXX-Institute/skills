"""Shared constants and helpers for automated MR reviews.

Used by both the posting script and compatibility readers of older Claude review
threads, so marker detection remains backward compatible.
"""

from __future__ import annotations

# Hidden marker embedded in the summary note so a given HEAD is reviewed once.
REVIEW_SUMMARY_MARKER = "<!-- claude-review:{sha} -->"
REVIEW_NOTE_MARKER = "<!-- axxx-review-audit -->"

SEVERITY_EMOJI = {
    "CRITICAL": "\U0001f6a8",  # 🚨
    "WARNING": "⚠️",  # ⚠️
    "SUGGESTION": "\U0001f4a1",  # 💡
}

# Unambiguous substrings that mark one note as automated review output. Severity
# labels are deliberately absent: humans commonly write "**CRITICAL**" too.
_REVIEW_MARKERS = (
    REVIEW_NOTE_MARKER,
    "<!-- claude-review:",
)


def is_claude_review_discussion(discussion: dict) -> bool:
    """True when the first note was authored by this review workflow."""
    notes = discussion.get("notes") or []
    if not notes:
        return False
    body = notes[0].get("body", "")
    return any(marker in body for marker in _REVIEW_MARKERS)


def iter_review_notes(discussions: list[dict], author_id: int | None):
    """Yield ``(discussion_id, note_id)`` for this bot's marked review notes."""
    for discussion in discussions:
        for note in discussion.get("notes") or []:
            if note.get("system"):
                continue
            if (note.get("author") or {}).get("id") != author_id:
                continue
            if not any(marker in note.get("body", "") for marker in _REVIEW_MARKERS):
                continue
            yield discussion["id"], note["id"]


def format_summary_body(sha: str, message: str) -> str:
    """Render a marked review summary that cleanup can identify safely."""
    summary_marker = REVIEW_SUMMARY_MARKER.format(sha=sha)
    return (
        f"{summary_marker}\n{REVIEW_NOTE_MARKER}\n\n"
        f"## Automated Code Review\n\n{message.strip()}\n"
    )


def format_inline_body(severity: str, message: str) -> str:
    """Render a marked inline-review body with an optional severity label."""
    sev = severity.upper()
    emoji = SEVERITY_EMOJI.get(sev, "")
    prefix = f"{emoji} **{sev}**: " if sev in SEVERITY_EMOJI else ""
    return f"{REVIEW_NOTE_MARKER}\n\n{prefix}{message}"


def summarize_inline_results(results: list[dict]) -> dict:
    """Aggregate inline publication results and fail if any write failed."""
    posted = sum(1 for result in results if result["status"] == "posted")
    skipped = sum(1 for result in results if result["status"] == "skipped")
    errors = sum(1 for result in results if result["status"] == "error")
    return {
        "status": "error" if errors else "ok",
        "posted": posted,
        "skipped": skipped,
        "errors": errors,
        "results": results,
    }


def summarize_cleanup_result(
    mr_iid: int, deleted: list[int], failed: list[dict]
) -> dict:
    """Build cleanup output and fail closed when any deletion failed."""
    return {
        "status": "error" if failed else "ok",
        "mr_iid": mr_iid,
        "deleted_count": len(deleted),
        "deleted_ids": deleted,
        "failed": failed,
    }
