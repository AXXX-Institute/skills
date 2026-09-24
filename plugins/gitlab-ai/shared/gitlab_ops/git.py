"""Git remote and branch helpers."""

from __future__ import annotations

import os
import re
import subprocess
import urllib.parse

# CI environment variables that carry the real branch name when the working tree
# is in a detached HEAD, in priority order: the merge-request source branch
# first (MR pipelines), then the branch-pipeline name. GitLab checks out a
# merge-request ref in a detached HEAD, so ``git rev-parse --abbrev-ref HEAD``
# yields ``"HEAD"`` and these are the only reliable source of the branch name.
_CI_BRANCH_ENV_VARS = (
    "CI_MERGE_REQUEST_SOURCE_BRANCH_NAME",
    "CI_COMMIT_BRANCH",
    "CI_COMMIT_REF_NAME",
)


def parse_remote_url(remote_url: str) -> tuple[str, str]:
    """Extract (gitlab_host, project_path) from git remote URL."""
    url = remote_url.strip()

    ssh_match = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    if url.startswith("ssh://"):
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname and parsed.path.strip("/"):
            path = re.sub(r"\.git$", "", parsed.path.strip("/"))
            return parsed.hostname, path

    url = re.sub(r"\.git$", "", url)
    url = re.sub(r"https?://[^@]+@", "https://", url)
    match = re.match(r"https?://([^/]+)/(.+)$", url)
    if match:
        return match.group(1), match.group(2)

    raise ValueError(f"Cannot parse git remote URL: {remote_url}")


def get_current_branch() -> str:
    """Return the current branch name.

    ``git rev-parse --abbrev-ref HEAD`` returns ``"HEAD"`` in a detached HEAD,
    which GitLab CI produces when it checks out a merge-request ref. In that case
    fall back to the CI-provided branch name (the MR source branch, or the
    branch-pipeline ref) so callers still resolve the real branch instead of the
    literal ``"HEAD"``.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    branch = result.stdout.strip()
    if branch == "HEAD":
        for var in _CI_BRANCH_ENV_VARS:
            value = os.getenv(var, "").strip()
            if value:
                return value
    return branch
