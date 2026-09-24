"""Shared constants and helpers for automated MR reviews.

Used by both the posting script and compatibility readers of older Claude review
threads, so marker detection remains backward compatible.
"""

from __future__ import annotations

# Hidden marker embedded in the summary note so a given HEAD is reviewed once.
REVIEW_SUMMARY_MARKER = "<!-- claude-review:{sha} -->"

SEVERITY_EMOJI = {
    "CRITICAL": "\U0001f6a8",  # 🚨
    "WARNING": "⚠️",  # ⚠️
    "SUGGESTION": "\U0001f4a1",  # 💡
}

# Substrings that mark a note as authored by this or an older review workflow.
_REVIEW_MARKERS = (
    "<!-- claude-review:",
    "## Claude Code Review",
    "## Automated Code Review",
    *(f"**{sev}**" for sev in SEVERITY_EMOJI),
)


def is_claude_review_discussion(discussion: dict) -> bool:
    """True when the first note was authored by this review workflow."""
    notes = discussion.get("notes") or []
    if not notes:
        return False
    body = notes[0].get("body", "")
    return any(marker in body for marker in _REVIEW_MARKERS)


def iter_review_notes(
    discussions: list[dict], author_id: int | None
):
    """Yield ``(discussion_id, note_id)`` for this bot's marked review notes."""
    for discussion in discussions:
        if not is_claude_review_discussion(discussion):
            continue
        for note in discussion.get("notes") or []:
            if note.get("system"):
                continue
            if (note.get("author") or {}).get("id") != author_id:
                continue
            yield discussion["id"], note["id"]


def format_inline_body(severity: str, message: str) -> str:
    """Render an inline-discussion body: ``🚨 **CRITICAL**: message``."""
    sev = severity.upper()
    emoji = SEVERITY_EMOJI.get(sev, "")
    prefix = f"{emoji} **{sev}**: " if sev in SEVERITY_EMOJI else ""
    return f"{prefix}{message}"
