# mlspace-jobs-scaffold

Add experiments-as-code MLSpace training and evaluation launchers to a project,
including dry-run verification, idempotency, deduplication, and immutable code
staging.

This skill belongs to the `mlspace-jobs` plugin.

[Open the skill page](https://axxx-institute.github.io/skills/mlspace-jobs-scaffold/)

## Install

### Claude Code

```text
/plugin marketplace add AXXX-Institute/skills
/plugin install mlspace-jobs@axxx-institute
```

### OpenAI Codex

```bash
codex plugin marketplace add AXXX-Institute/skills
codex plugin add mlspace-jobs@axxx-institute
```

## Use

- Claude Code: `/mlspace-jobs:mlspace-jobs-scaffold`
- OpenAI Codex: `$mlspace-jobs:mlspace-jobs-scaffold`

Ask it to set up MLSpace launchers in the current repository. It creates and
tests launchers but does not submit a real GPU job. See [SKILL.md](SKILL.md).
