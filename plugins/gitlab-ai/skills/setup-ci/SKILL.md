---
name: setup-ci
description: Connect a repository to the gitlab-ai review and agent-audit GitLab CI jobs. Use when asked to add, enable, configure, or explain gitlab-ai CI for a repository; do not use merely to diagnose an already-configured failed pipeline.
---

# Set up gitlab-ai CI

Read [references/ci-setup.md](references/ci-setup.md) before acting.

When the user asks only how to connect a repository, present the minimal config
and secret requirements without editing files. When they ask to set it up,
inspect the existing `.gitlab-ci.yml`, preserve its jobs/includes/variables, and
add the ci-tools include plus `CI_TOOLS_RUNNER_TAG` using the reference rules.

Repository edits are authorized by an explicit setup/connect request. Do not
create tokens, change GitLab project settings, or trigger a pipeline unless the
user separately authorizes that external mutation. Finish by showing what was
changed, what secret still needs to be configured, and how the configuration was
validated.
