"""GitLab authentication, session, logging, and project resolution."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
from typing import NoReturn

import requests

from .git import get_current_branch, parse_remote_url


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def gitlab_headers() -> dict[str, str]:
    for var in ("MR_AUTO_REVIEW_GITLAB_TOKEN", "GITLAB_TOKEN"):
        token = os.getenv(var, "").strip()
        if token:
            log(f"  Using {var}")
            return {"PRIVATE-TOKEN": token}
    return {}


def gitlab_error(msg: str) -> NoReturn:
    """Write a JSON error to stdout and exit."""
    json.dump({"status": "error", "message": msg}, sys.stdout, indent=2)
    print()
    sys.exit(0)


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def resolve_project() -> tuple[str, str, str]:
    """Resolve GitLab base_url, project_id, and branch from git state.

    Calls gitlab_error() on failure (does not return).
    Returns (base_url, project_id, branch).
    """
    headers = gitlab_headers()
    if not headers:
        gitlab_error(
            "No GitLab token found. "
            "Set MR_AUTO_REVIEW_GITLAB_TOKEN or GITLAB_TOKEN env var."
        )

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        host, project_path = parse_remote_url(result.stdout)
    except (subprocess.CalledProcessError, ValueError) as exc:
        gitlab_error(f"Cannot determine GitLab project from git remote: {exc}")

    base_url = f"https://{host}/api/v4"
    project_id = urllib.parse.quote(project_path, safe="")
    log(f"  Project: {host}/{project_path}")

    try:
        branch = get_current_branch()
    except subprocess.CalledProcessError:
        gitlab_error("Cannot determine current git branch.")

    if branch in ("main", "master", "HEAD"):
        gitlab_error(f"Current branch is '{branch}' — switch to a feature branch.")

    log(f"  Branch: {branch}")
    return base_url, project_id, branch
