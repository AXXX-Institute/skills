# adversarial-review

Run an independent, fresh-context review of a committed implementation across
every affected usage path. The reviewer returns an `APPROVE` or `REVISE`
verdict and never edits the change it judges.

This skill is explicit-only and belongs to the `adversarial-review` plugin.

[Open the skill page](https://axxx-institute.github.io/skills/adversarial-review/)

## Install

### Claude Code

```text
/plugin marketplace add AXXX-Institute/skills
/plugin install adversarial-review@axxx-institute
```

### OpenAI Codex

```bash
codex plugin marketplace add AXXX-Institute/skills
codex plugin add adversarial-review@axxx-institute
```

## Use

- Claude Code: `/adversarial-review`
- OpenAI Codex: `$adversarial-review`

Invoke it after committing a non-trivial implementation. See [SKILL.md](SKILL.md)
for the review contract and delegation requirements.
