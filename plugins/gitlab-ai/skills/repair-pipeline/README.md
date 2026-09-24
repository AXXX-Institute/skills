# repair-pipeline

Inspect the latest GitLab pipeline for the current branch, retrieve failed-job
logs, distinguish code failures from infrastructure failures, and repair
actionable problems.

This skill belongs to the `gitlab-ai` plugin.

[Open the skill page](https://axxx-institute.github.io/skills/repair-pipeline/)

## Install

### Claude Code

```text
/plugin marketplace add AXXX-Institute/skills
/plugin install gitlab-ai@axxx-institute
```

### OpenAI Codex

```bash
codex plugin marketplace add AXXX-Institute/skills
codex plugin add gitlab-ai@axxx-institute
```

## Use

- Claude Code: `/gitlab-ai:repair-pipeline`
- OpenAI Codex: `$gitlab-ai:repair-pipeline`

Run it from the repository whose branch or merge request should be diagnosed.
See [SKILL.md](SKILL.md) for waiting and repair behavior.
