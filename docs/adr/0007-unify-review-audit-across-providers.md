# ADR 0007: Unify review and audit across providers

## Status

Accepted.

## Context

The original ci-tools workflows exposed separate Claude and Codex skill files
for the same jobs. Their orchestration primitives differ, but their review
severity contract, GitLab posting behavior, audit evidence rules, and model
roles are the same. Maintaining whole provider-specific copies lets those
contracts drift.

## Decision

Publish one independently installable `review-audit` plugin containing two
provider-neutral skills: `review-mr` and `agent-config-audit`.

Each skill detects the active provider only at its delegation boundary. Shared
model resolution and deterministic GitLab helpers live once under the plugin's
`shared/` directory. The model policy is task-first (`review` and `audit`) with
optional provider-specific overrides.

Keep the existing ci-tools vendored commands as compatibility entry points for
consumer CI. The marketplace plugin is the preferred interactive installation
path; it does not depend on a ci-tools checkout at runtime.

## Consequences

- Claude Code and Codex load the same `SKILL.md` files.
- Review and audit behavior evolves in one place, while provider-specific
  delegation remains explicit and testable.
- The plugin duplicates a small deterministic helper library from ci-tools so
  an installed plugin is self-contained. Updates must be synchronized until
  ci-tools consumers migrate to the plugin distribution path.
