# review-mr

Review the current branch's GitLab merge request, replace prior bot feedback,
post a summary and CRITICAL inline discussions, and emit a CI-compatible
verdict.

This skill belongs to the `gitlab-ai` plugin.

[Open the skill page](https://axxx-institute.github.io/skills/review-mr/)

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

- Claude Code: `/gitlab-ai:review-mr`
- OpenAI Codex: `$gitlab-ai:review-mr`

Publishing requires explicit user intent. See [SKILL.md](SKILL.md) and the
plugin's shared review reference for the complete workflow.
