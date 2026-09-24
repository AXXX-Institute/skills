---
name: audit-agent-config
description: Audit and optionally repair repository-scoped Claude Code and Codex guidance by verifying claims against source code. Use when asked to check, validate, sync, or update CLAUDE.md, AGENTS.md, project skills, commands, or stale agent documentation.
---

# Audit repository agent configuration

Verify project-owned agent guidance against source code. A claim is stale only
when concrete repository evidence contradicts it; missing corroboration is not a
contradiction.

## Scope

Audit repository-scoped files only:

- every `CLAUDE.md` and `AGENTS.md`, respecting nested-file scope;
- project-authored files under `.claude/skills/`, `.claude/commands/`,
  `.codex/skills/`, and `.agents/skills/`;
- supporting references or scripts when a scoped skill makes claims about them.

Exclude user-global configuration, installed plugin caches, and vendored
third-party skill/command directories. When the repository documents a vendored
ownership boundary, honor it.

## Choose audit workers

Resolve `<skill-dir>` to the directory containing this file and `<plugin-dir>` to
its `../..` parent. Infer the active provider and run:

```bash
bash <plugin-dir>/shared/model_policy.sh audit <provider>
```

Enumerate scoped files before reading them all. When delegation is available,
assign one file per fresh-context worker up to the concurrency limit, pass the
resolved model, and replenish the queue as workers finish. Otherwise inspect
sequentially and disclose that the configured worker model could not be applied.

For each file, verify paths, package responsibilities, named symbols, imports,
deprecations, environment variables, and configuration mappings against source.
Return `STALE`, `VERIFIED`, and `UNABLE TO VERIFY` findings. Every STALE entry
must quote the claim and cite concrete contradictory `file:line` evidence.
Interpret ambiguous wording charitably and never judge one guidance file merely
by another.

Re-check every proposed STALE item in the parent session. Then scan the primary
source-tree layout for structurally significant undocumented packages; do not
report individual files inside an already documented package tree as omissions.

## Report and repair

Report each audited file with STALE, OMISSIONS, VERIFIED, and UNABLE TO VERIFY
sections, followed by a summary table. Report only by default. Repair confirmed
stale claims and significant omissions only when the user explicitly asks to
fix, update, repair, or sync the guidance. Repairs must be minimal: do not
rewrite accurate prose or change source code to make documentation true.

The final output line must be bare:

```text
AUDIT_VERDICT: PASS
```

Use `AUDIT_VERDICT: FAIL (<n> stale, <m> omissions)` while any confirmed stale
claim or omission remains.
