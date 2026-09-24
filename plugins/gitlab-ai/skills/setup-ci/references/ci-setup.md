# Connect a repository to gitlab-ai CI

## Minimal repository configuration

Merge this entry into the repository's `.gitlab-ci.yml`:

```yaml
include:
  - project: fusionbrain/multimodal/research-agent/ci-tools
    ref: main
    file: ci/ci-tools.yml

variables:
  CI_TOOLS_RUNNER_TAG: "<runner-tag>"
```

This contributes `claude-audit` and `auto-review` in GitLab's built-in `.post`
stage, so do not add or reorder stages solely for gitlab-ai.

## Safe merge rules

- Preserve every existing job, include, variable, workflow rule, default, and
  stage declaration.
- If `include` is already a list, append the ci-tools mapping unless the same
  project/ref/file tuple already exists. If it is a scalar or mapping, convert
  it to a list containing both the existing value and the new mapping.
- If `variables` exists, add only missing ci-tools keys. Never replace unrelated
  variables or a deliberate existing ci-tools override.
- Reuse an existing non-variable runner tag when one tag is clearly common to
  the repository's jobs. Reuse an existing `CI_TOOLS_RUNNER_TAG` unchanged.
  Otherwise ask the user for the runner tag; do not guess one from another
  repository or bake in `dtarasov-debug`.
- Add `CI_TOOLS_BIN_PATH` only when the runner does not already find `claude`
  and `uv` on `PATH`.

## GitLab project secret

In **Settings → CI/CD → Variables**, add one masked variable:

- `MR_AUTO_REVIEW_GITLAB_TOKEN` (preferred), or `GITLAB_TOKEN`;
- value: a GitLab token allowed to read the project and its pipelines and to
  create/delete merge-request notes and discussions.

Do not put the token in `.gitlab-ci.yml` or any committed file. Mark it
protected only when the project's protected-variable policy still exposes it to
the merge-request pipelines that must run these jobs.

The GitLab API host and project path come from the repository's `origin` remote;
no host variable is normally required.

## Validate and report

After editing:

1. Parse the YAML locally when a YAML parser is available.
2. Use `glab ci lint` when `glab` is authenticated and supports it; linting is
   read-only. Otherwise report that server-side lint was not run.
3. Show the exact diff. Do not commit unless requested or repository guidance
   requires implementation commits.
4. Remind the user to add the masked token if it cannot be verified without
   exposing its value. Never print or retrieve the token itself.
