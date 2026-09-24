"""GitLab REST API request helpers."""

from __future__ import annotations

import re

from .auth import gitlab_headers, log, new_session


def gitlab_get(base_url: str, project_id: str, endpoint: str) -> list[dict]:
    """Paginated GET from GitLab API."""
    headers = gitlab_headers()
    separator = "&" if "?" in endpoint else "?"
    url = f"{base_url}/projects/{project_id}/{endpoint}{separator}per_page=100"
    results: list[dict] = []
    session = new_session()

    while url:
        log(f"  GET {url}")
        resp = session.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            results.extend(data)
        else:
            results.append(data)
        next_page = resp.headers.get("x-next-page", "").strip()
        if next_page:
            base = re.sub(r"[&?]page=\d+", "", url)
            sep = "&" if "?" in base else "?"
            url = f"{base}{sep}page={next_page}"
        else:
            url = None
    return results


def gitlab_get_text(base_url: str, project_id: str, endpoint: str) -> str:
    """GET raw text from GitLab API (for job logs)."""
    headers = gitlab_headers()
    url = f"{base_url}/projects/{project_id}/{endpoint}"
    session = new_session()
    log(f"  GET {url}")
    resp = session.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def _gitlab_write(
    base_url: str, project_id: str, endpoint: str, method: str, body: dict
) -> dict:
    """POST/PUT JSON to the GitLab API and return the parsed response (if any)."""
    headers = gitlab_headers()
    headers["Content-Type"] = "application/json"
    url = f"{base_url}/projects/{project_id}/{endpoint}"
    session = new_session()
    log(f"  {method} {url}")
    resp = session.request(method, url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json() if resp.text else {}


def gitlab_post(base_url: str, project_id: str, endpoint: str, body: dict) -> dict:
    """POST JSON to the GitLab API."""
    return _gitlab_write(base_url, project_id, endpoint, "POST", body)


def gitlab_put(base_url: str, project_id: str, endpoint: str, body: dict) -> dict:
    """PUT JSON to the GitLab API."""
    return _gitlab_write(base_url, project_id, endpoint, "PUT", body)


def gitlab_delete(base_url: str, project_id: str, endpoint: str) -> None:
    """DELETE a project resource (e.g. an MR discussion note)."""
    headers = gitlab_headers()
    url = f"{base_url}/projects/{project_id}/{endpoint}"
    session = new_session()
    log(f"  DELETE {url}")
    resp = session.delete(url, headers=headers, timeout=30)
    resp.raise_for_status()


def gitlab_get_self(base_url: str) -> dict:
    """GET the authenticated user (used to identify the token/bot's own notes)."""
    headers = gitlab_headers()
    url = f"{base_url}/user"
    session = new_session()
    log(f"  GET {url}")
    resp = session.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()
