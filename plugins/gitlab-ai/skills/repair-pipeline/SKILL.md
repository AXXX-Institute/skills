---
name: repair-pipeline
description: Diagnose the latest GitLab pipeline on the current branch and repair actionable failures. Use when asked to inspect, debug, or fix a failed GitLab CI pipeline; do not use for unrelated local test failures.
---

# Repair a GitLab pipeline

Fetch failed job logs from the latest pipeline on this branch's GitLab MR and fix the errors.

## Step 1: Fetch pipeline data (wait for it to finish, in the background)

Run the fetch script with `--wait`; when the host supports background commands,
launch it in the background so it can wait without blocking other work:

```
uv run <skill-dir>/scripts/fetch_pipeline.py --wait
```

`<skill-dir>` is the **absolute path of the directory containing this SKILL.md**.
Never substitute a repository-relative path: installed plugin files live outside
the repository being repaired. Run the script from the target repository because
its Git remote and current branch select the merge request and pipeline.

Wait for the command to complete and read its stdout. `--wait` polls every 15s
(≤30 min) while the
pipeline is `created/pending/running/scheduled/…`, returning as soon as it is
`success/failed/canceled/skipped/manual` (`manual` = the automatic `check` stage
finished and the `review` stage is manual-gated). Diagnostics go to stderr; the
JSON result goes to stdout.

Parse the JSON output:
- If `status` is `"error"`, tell the user the error message and stop.
- If `timed_out` is `true`, tell the user the pipeline was still running after the
  timeout and report the partial status; offer to wait again.

(For an immediate, non-blocking snapshot, run without `--wait`.)

## Step 2: Present the pipeline status

Show the user:
- MR title and link (if any)
- Pipeline ID, status, and link
- Pipeline commit SHA
- Number of failed jobs

If there are no failed jobs, tell the user the pipeline is green and stop.

## Step 3: Analyze and fix failures

For each failed job:
1. Show the job name, stage, and link
2. Analyze the log tail to identify the root cause of the failure
3. Determine if this is a code issue that can be fixed (vs infrastructure/flaky/timeout)
4. If fixable:
   - Read the referenced file(s) around the error location
   - Apply the fix using the Edit tool
   - Briefly explain what you changed and why
5. If not fixable (infra issue, timeout, flaky test, etc.):
   - Explain why it can't be fixed in code
   - Suggest what the user can do (retry, check infra, etc.)

Filter based on $ARGUMENTS if provided:
- A job name — only fix that specific job
- If empty — fix all failed jobs

## Step 4: Summary

After all analysis, show a table: job name, stage, root cause, what was done.

Do not commit unless the user also asked you to commit or the repository's
instructions require commits for implementation work.
