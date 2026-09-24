---
name: review-mr
description: Review the current branch's GitLab merge request, replace prior bot feedback, post a summary plus CRITICAL inline discussions, and emit a CI-compatible verdict. Use for MR review or auto-review requests in Claude Code or Codex.
---

# Review a GitLab merge request

Resolve `<plugin-dir>` to this skill directory's `../..` parent. Read and follow
the complete shared workflow at
`<plugin-dir>/shared/references/review-mr.md`. The workflow is shared unchanged
between Claude Code and Codex and gates GitLab mutations on explicit user intent.
