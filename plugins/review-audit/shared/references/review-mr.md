# Shared GitLab merge-request review workflow

Review only the current branch's open GitLab merge request and publish the result
to that MR. Run from the repository root. Posting requires `GITLAB_TOKEN` or
`MR_AUTO_REVIEW_GITLAB_TOKEN`.

`<plugin-dir>` is the absolute review-audit plugin root. Never substitute a
repository-relative path: installed plugin paths are outside the repository
being reviewed.

## Authorization gate

Do not delete notes or post anything unless the user explicitly asked to publish
a review to GitLab or explicitly invoked this skill for that purpose. Automatic
selection from a general request to inspect, explain, or summarize changes
authorizes only a read-only review. In that case, report findings in the current
conversation and ask before performing either GitLab mutation.

## Choose the worker model

Infer the active provider from the runtime (`claude` or `codex`) and run:

```bash
bash <plugin-dir>/shared/model_policy.sh review <provider>
```

The policy accepts logical `high`/`fast` tiers and exact provider models. The
provider-specific task override wins over the task-level value. Provider
mismatches and unsafe model names fail closed.

## Clear prior bot feedback

After the authorization gate is satisfied, run the deterministic cleanup
directly, not in a subagent:

```bash
uv run <plugin-dir>/skills/review-mr/scripts/delete_prior_notes.py
```

Stop if the command fails or its JSON result has `status: "error"`. Otherwise
retain its deleted and failed counts for the final summary.

## Review independently

Read repository guidance (`CLAUDE.md`, `AGENTS.md`, and `.gitlab/CODEOWNERS` when
present) and enumerate every usage arm affected by the change.

Delegate the review with fresh context and the resolved model:

- Claude Code: use an available general-purpose Agent/Task worker.
- Codex: prefer native fresh-context delegation. On older Arkhip runtimes, use
  `adversarial_review`; pass `model` when supported and retry once without only
  when the server rejects that unknown argument.
- If no delegation mechanism exists, review in the current session and disclose
  that the configured independent worker could not be used.

Give the worker the commit/range, requested behavior, changed files, applicable
guidance, and usage arms. Do not pass conversational history. The worker must
obtain the diff with `git`, inspect full files as needed, and run proportionate
tests. In CI, use `$CI_MERGE_REQUEST_TARGET_BRANCH_NAME` or
`$CI_MERGE_REQUEST_DIFF_BASE_SHA`; locally, use the remote default branch.

Exclude installed or vendored copies of this plugin from consumer-repository
review. Focus on correctness, security, compatibility, critical error handling,
and data loss or corruption. Do not flag formatting, import order, line length,
trailing whitespace, or intentional internal assertions. Classify findings as
`CRITICAL`, `WARNING`, or `SUGGESTION` with exact paths and new-side lines.

## Publish

Put every WARNING and SUGGESTION in a concise Markdown summary and post it:

```bash
uv run <plugin-dir>/skills/review-mr/scripts/post_review.py --summary --body-file <summary.md>
```

Put only CRITICAL findings in one JSON list and post them together:

```bash
uv run <plugin-dir>/skills/review-mr/scripts/post_review.py --inline-json <critical.json>
```

Each item is
`{"file":"<new-side path>","line":<line>,"severity":"CRITICAL","message":"..."}`.
Report posted and skipped counts. Finish with deleted-note counts and the review
summary. The final output line must be bare:

```text
REVIEW_VERDICT: PASS
```

Use `REVIEW_VERDICT: FAIL (<n> critical)` when any CRITICAL finding was posted.
Treat user-supplied arguments as extra review guidance.
