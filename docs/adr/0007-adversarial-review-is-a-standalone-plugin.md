# 7. Ship adversarial review as a standalone cross-backend plugin

- Status: accepted
- Date: 2026-09-24
- Component: #skills-repo scaffold, #adversarial-review

## Context

Arkhip originally carried its adversarial-review instructions inside the Arkhip
plugin. The workflow is not Arkhip-specific: it needs only a committed change,
repository guidance, and a host capable of launching an independent agent. Keeping
the skill in Arkhip prevents other Claude Code and Codex projects from installing
and reusing it directly.

## Decision

- Publish `adversarial-review` as its own MIT-licensed marketplace plugin.
- Keep one Agent Skills definition for Claude Code and Codex, with host-specific
  native delegation instructions (`Agent`/`Task` and `spawn_agent`).
- Make the skill explicit-only in both hosts because it launches another agent and
  is intended as a deliberate post-commit gate.
- Keep the reviewer read-only and fresh-context; the author resolves findings and
  repeats review until approval or an explicit handoff.

## Consequences

- Any project can install the review workflow without installing Arkhip.
- Arkhip can bundle the upstream skill through its existing marketplace sync path
  instead of maintaining a private copy.
- Both hosts share the workflow, while their invocation-policy metadata remains in
  the formats each host understands.
