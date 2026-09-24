# audit-agent-config

Audit repository-owned Claude Code and Codex guidance against source code, then
report or optionally repair confirmed stale claims.

This skill belongs to the `gitlab-ai` plugin.

[Open the skill page](https://axxx-institute.github.io/skills/audit-agent-config/)

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

- Claude Code: `/gitlab-ai:audit-agent-config`
- OpenAI Codex: `$gitlab-ai:audit-agent-config`

The default mode is report-only; repairs require an explicit request. See
[SKILL.md](SKILL.md) for scope and evidence requirements.
