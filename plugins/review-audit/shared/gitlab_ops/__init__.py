"""Shared GitLab API helpers for CI scripts.

Bundled into the review-audit plugin. Imported as a plain package off
``sys.path`` (the scripts add the plugin's ``shared`` dir) — it is NOT installed via pip.
Its only third-party dependency is ``requests`` (supplied by each script's
PEP 723 header under ``uv run``).
"""

from .api import (
    gitlab_delete,
    gitlab_get,
    gitlab_get_self,
    gitlab_get_text,
    gitlab_post,
    gitlab_put,
)
from .git import (
    get_current_branch,
    parse_remote_url,
)
from .auth import (
    gitlab_error,
    gitlab_headers,
    log,
    resolve_project,
)
from .diff import (
    build_diff,
    collect_changed_lines,
)
from .mr import (
    delete_discussion_note,
    fetch_diff_versions,
    fetch_mr_changes,
    fetch_mr_discussions,
    find_mr,
    post_inline_discussion,
    post_note,
    resolve_discussion,
)
from .review import (
    REVIEW_NOTE_MARKER,
    REVIEW_SUMMARY_MARKER,
    SEVERITY_EMOJI,
    format_inline_body,
    format_summary_body,
    is_claude_review_discussion,
    iter_review_notes,
)

__all__ = [
    "REVIEW_NOTE_MARKER",
    "REVIEW_SUMMARY_MARKER",
    "SEVERITY_EMOJI",
    "build_diff",
    "collect_changed_lines",
    "delete_discussion_note",
    "fetch_diff_versions",
    "fetch_mr_changes",
    "fetch_mr_discussions",
    "find_mr",
    "format_inline_body",
    "format_summary_body",
    "get_current_branch",
    "gitlab_delete",
    "gitlab_error",
    "gitlab_get",
    "gitlab_get_self",
    "gitlab_get_text",
    "gitlab_headers",
    "gitlab_post",
    "gitlab_put",
    "is_claude_review_discussion",
    "iter_review_notes",
    "log",
    "parse_remote_url",
    "post_inline_discussion",
    "post_note",
    "resolve_discussion",
    "resolve_project",
]
