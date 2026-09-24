#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "python-dotenv"]
# ///
"""Fetch failed job logs from the latest pipeline on the current branch's GitLab MR.

Outputs JSON to stdout. Diagnostics go to stderr.
Run with: uv run <skill-dir>/scripts/fetch_pipeline.py [--wait]
Requires GITLAB_TOKEN or MR_AUTO_REVIEW_GITLAB_TOKEN env var.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import urllib.parse

from dotenv import load_dotenv

# Import the helper package bundled once at the gitlab-ai plugin root.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "shared"))

load_dotenv()

from gitlab_ops import (  # noqa: E402
    find_mr,
    gitlab_get,
    gitlab_get_text,
    log,
    resolve_project,
)

# Pipeline statuses that are not yet final — keep polling while in one of these.
ACTIVE_STATUSES = {
    "created",
    "waiting_for_resource",
    "preparing",
    "pending",
    "running",
    "scheduled",
}


# ---------------------------------------------------------------------------
# Pipeline + jobs lookup
# ---------------------------------------------------------------------------


def find_latest_pipeline(
    base_url: str, project_id: str, branch: str, mr_iid: int | None = None
) -> dict | None:
    """Find the most recent pipeline for the given branch.

    Tries three strategies:
    1. MR pipelines API (most comprehensive when MR exists — includes all triggered pipelines)
    2. Filter by branch ref
    3. Filter by MR merge-request ref (refs/merge-requests/<iid>/head)
    """
    encoded_branch = urllib.parse.quote(branch, safe="/")

    # Strategy 1: MR pipelines API (most comprehensive for MR-associated pipelines)
    if mr_iid:
        pipelines = gitlab_get(
            base_url,
            project_id,
            f"merge_requests/{mr_iid}/pipelines?order_by=id&sort=desc",
        )
        if pipelines:
            log(f"  Found {len(pipelines)} pipelines via MR API")
            return pipelines[0]

    # Strategy 2: direct branch ref
    pipelines = gitlab_get(
        base_url,
        project_id,
        f"pipelines?ref={encoded_branch}&order_by=id&sort=desc",
    )
    if pipelines:
        log(f"  Found {len(pipelines)} pipelines via branch ref")
        return pipelines[0]

    # Strategy 3: MR ref format (refs/merge-requests/<iid>/head)
    if mr_iid:
        mr_ref = f"refs/merge-requests/{mr_iid}/head"
        encoded_mr_ref = urllib.parse.quote(mr_ref, safe="/")
        pipelines = gitlab_get(
            base_url,
            project_id,
            f"pipelines?ref={encoded_mr_ref}&order_by=id&sort=desc",
        )
        if pipelines:
            log(f"  Found {len(pipelines)} pipelines via MR ref")
            return pipelines[0]

    return None


def get_pipeline_jobs(base_url: str, project_id: str, pipeline_id: int) -> list[dict]:
    """Get all jobs for a pipeline."""
    return gitlab_get(
        base_url,
        project_id,
        f"pipelines/{pipeline_id}/jobs",
    )


def get_job_log(
    base_url: str, project_id: str, job_id: int, tail_lines: int = 150
) -> str:
    """Fetch job log and return the last N lines."""
    log_text = gitlab_get_text(base_url, project_id, f"jobs/{job_id}/trace")
    # Strip ANSI escape codes
    log_text = re.sub(r"\x1b\[[0-9;]*m", "", log_text)
    lines = log_text.splitlines()
    if len(lines) > tail_lines:
        lines = lines[-tail_lines:]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Waiting
# ---------------------------------------------------------------------------


def wait_for_pipeline(
    base_url: str,
    project_id: str,
    branch: str,
    mr_iid: int | None,
    interval: int,
    timeout: int,
) -> tuple[dict | None, bool]:
    """Poll the latest pipeline until it leaves an active status.

    Re-resolves the latest pipeline each iteration so a newly-pushed pipeline
    supersedes an older one. ``manual`` counts as finished: the automatic
    ``check`` stage is done and the ``review`` stage is manual-gated.

    Returns ``(pipeline, timed_out)``. ``pipeline`` is ``None`` if none exists.
    """
    deadline = time.monotonic() + timeout
    while True:
        pipeline = find_latest_pipeline(base_url, project_id, branch, mr_iid)
        if not pipeline:
            return None, False
        status = pipeline.get("status", "unknown")
        if status not in ACTIVE_STATUSES:
            return pipeline, False
        if time.monotonic() >= deadline:
            log(f"  Timed out after {timeout}s while pipeline was '{status}'")
            return pipeline, True
        log(f"  Pipeline #{pipeline['id']} is '{status}', waiting {interval}s…")
        time.sleep(interval)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Poll until the pipeline finishes before reporting failed jobs.",
    )
    parser.add_argument(
        "--interval", type=int, default=15, help="Polling interval in seconds."
    )
    parser.add_argument(
        "--timeout", type=int, default=1800, help="Max seconds to wait (--wait)."
    )
    args = parser.parse_args()

    base_url, project_id, branch = resolve_project()

    # Find MR
    mr = find_mr(base_url, project_id, branch)
    mr_iid = mr["iid"] if mr else None
    mr_title = mr.get("title", "") if mr else ""
    mr_url = mr.get("web_url", "") if mr else ""
    if mr:
        log(f"  MR !{mr_iid}: {mr_title}")

    # Find latest pipeline (optionally waiting for it to finish)
    timed_out = False
    if args.wait:
        pipeline, timed_out = wait_for_pipeline(
            base_url, project_id, branch, mr_iid, args.interval, args.timeout
        )
    else:
        pipeline = find_latest_pipeline(base_url, project_id, branch, mr_iid)
    if not pipeline:
        json.dump(
            {
                "status": "error",
                "message": f"No pipelines found for branch '{branch}'.",
            },
            sys.stdout,
            indent=2,
        )
        print()
        sys.exit(0)

    pipeline_id = pipeline["id"]
    pipeline_status = pipeline.get("status", "unknown")
    pipeline_url = pipeline.get("web_url", "")
    pipeline_sha = pipeline.get("sha", "")
    log(f"  Pipeline #{pipeline_id}: {pipeline_status} ({pipeline_sha})")

    # Get jobs
    jobs = get_pipeline_jobs(base_url, project_id, pipeline_id)
    failed_jobs = [j for j in jobs if j.get("status") == "failed"]

    if not failed_jobs:
        output = {
            "status": "ok",
            "mr_iid": mr_iid,
            "mr_title": mr_title,
            "mr_url": mr_url,
            "pipeline_id": pipeline_id,
            "pipeline_status": pipeline_status,
            "pipeline_url": pipeline_url,
            "pipeline_sha": pipeline_sha,
            "timed_out": timed_out,
            "failed_jobs": [],
        }
        json.dump(output, sys.stdout, indent=2)
        print()
        return

    # Fetch logs for failed jobs
    failed_job_data = []
    for job in failed_jobs:
        job_id = job["id"]
        job_name = job.get("name", "unknown")
        job_stage = job.get("stage", "unknown")
        log(f"  Fetching log for failed job: {job_name} (#{job_id})")
        try:
            log_tail = get_job_log(base_url, project_id, job_id)
        except Exception as exc:
            log_tail = f"[Failed to fetch log: {exc}]"
        failed_job_data.append(
            {
                "job_id": job_id,
                "job_name": job_name,
                "stage": job_stage,
                "job_url": job.get("web_url", ""),
                "log_tail": log_tail,
            }
        )

    output = {
        "status": "ok",
        "mr_iid": mr_iid,
        "mr_title": mr_title,
        "mr_url": mr_url,
        "pipeline_id": pipeline_id,
        "pipeline_status": pipeline_status,
        "pipeline_url": pipeline_url,
        "pipeline_sha": pipeline_sha,
        "timed_out": timed_out,
        "failed_jobs": failed_job_data,
    }
    json.dump(output, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
