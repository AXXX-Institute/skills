# setup-ci

Connect a repository to the shared GitLab merge-request review and agent-audit
CI jobs without replacing its existing pipeline configuration.

This skill belongs to the `gitlab-ai` plugin.

[Open the skill page](https://axxx-institute.github.io/skills/setup-ci/)

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

- Claude Code: `/gitlab-ai:setup-ci`
- OpenAI Codex: `$gitlab-ai:setup-ci`

The skill preserves existing YAML, resolves the runner tag, validates the
result, and explains the masked token variable that must be configured in
GitLab. See [SKILL.md](SKILL.md) for its authorization boundary.
