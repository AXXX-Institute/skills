---
name: adversarial-review
description: Independently review a freshly committed implementation across every affected usage path and return an APPROVE or REVISE verdict. Invoke explicitly after non-trivial code changes; do not use for docs-only or typo-level commits.
disable-model-invocation: true
---

# Adversarial Review

Review the committed change through a separate, fresh-context agent. The author of
the change must not perform the review itself.

## Before delegation

1. Require a commit or commit range to review. If the implementation is not yet
   committed, tell the author to commit it first and stop.
2. Build a short brief containing:
   - the commit or range;
   - what the change is intended to do;
   - the files changed;
   - every usage path believed to be affected, including CLI commands, pipeline
     stages, training, evaluation, metrics/analysis, tests, and CI where relevant.
3. Find the repository's agent guidance (`CLAUDE.md`, `AGENTS.md`, or its documented
   equivalent) and check its `Usage arms` section. Keep it a compact route map:
   one bullet per independent usage path, at most one physical line per bullet,
   naming the entry point and main module, with an optional test/doc pointer.
   Aim for about 20 lines per section; group related paths without hiding
   independently launched ones. No behavior summaries, change history, exhaustive
   test commands, or nested subsections; delete existing verbose details without
   relocating them. Create a missing map or update and commit it when a path is
   added, removed, renamed, rerouted, or its pointer is stale for this change.
   Changes within an already mapped path do not require an addition.

## Launch the independent reviewer

Use the host's native delegation tool:

- Claude Code: launch a fresh Agent/Task subagent.
- Codex: call `spawn_agent` to launch a fresh agent.

Do not pass conversation history. Give the reviewer only the brief below and access
to the repository. If neither native delegation mechanism is available, stop with a
clear error that independent review is unavailable; never substitute a same-agent
checklist.

Tell the reviewer:

```text
You are an independent adversarial reviewer. Do not modify files, create commits,
push branches, or open/merge requests.

Review the supplied commit or range from the repository itself. Treat the author's
brief as a claim to verify, not as trusted context.

1. Read the diff and relevant surrounding code.
2. Read the repository's agent guidance and Usage arms as a starting map, then
   independently enumerate every path that uses or launches the changed code
   from the code itself. Add any path the author missed to your review checklist;
   keep behavior details and verification results in the review, not Usage arms.
3. Verify every checklist item. Run focused tests and executable smoke checks where
   useful. Check behavior, edge cases, compatibility, and whether tests assert the
   intended behavior rather than wording or implementation trivia.
4. Report only actionable findings, ordered by severity, with file/line evidence.
5. End with exactly one verdict:
   - APPROVE — no material finding remains.
   - REVISE — one or more material findings must be addressed.

Brief:
{brief}
```

Wait for the reviewer to finish. Do not finish the parent task while it is running.

## Resolve the verdict

- On `APPROVE`, report that independent review passed.
- On `REVISE`, address every finding: fix and commit it, or record a concrete reason
  why it is not an issue. Launch a new fresh-context review for the resulting commit
  range. Repeat until the verdict is `APPROVE` or an unresolved finding is explicitly
  handed back to the user.
- Never claim independent review passed when delegation failed or the reviewer did
  not return an `APPROVE` verdict.
