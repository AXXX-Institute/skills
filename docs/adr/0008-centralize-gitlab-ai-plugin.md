# ADR 0008: Centralize GitLab agent workflows in gitlab-ai

## Status

Accepted.

## Context

The initial provider-neutral plugin covered merge-request review and agent
configuration audit, while pipeline diagnosis remained a ci-tools-only skill.
ci-tools also retained full vendored copies of the review and audit workflows,
requiring manual synchronization between two sources of truth.

## Decision

Rename the plugin to `gitlab-ai` and use short verb-object skill names:
`setup-ci`, `review-mr`, `repair-pipeline`, and `audit-agent-config`.

The plugin owns the skill instructions, model policy, deterministic GitLab
helpers, and small headless-CI result/verdict parsers. ci-tools installs the
published plugin when needed, resolves its installation path, and invokes these
canonical assets; it does not vendor or snapshot plugin files.

## Consequences

- Claude Code and Codex expose the same four workflows from one plugin.
- Pipeline repair becomes independently installable outside ci-tools.
- ci-tools consumers need network access to GitHub during first installation.
- An already-installed plugin is reused, so updating it remains an explicit
  operator action rather than an implicit change during every pipeline.
- The old plugin and skill names are removed before their initial release; no
  marketplace compatibility aliases are required.
