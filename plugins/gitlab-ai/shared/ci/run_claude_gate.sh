#!/usr/bin/env bash
# Run one gitlab-ai skill as a fail-closed Claude CI gate.
#
# Usage: run_claude_gate.sh <review|audit> <prompt> <allowed-tools>
set -uo pipefail

task="${1:?usage: run_claude_gate.sh <review|audit> <prompt> <allowed-tools>}"
prompt="${2:?missing prompt}"
allowed_tools="${3:?missing allowed-tools list}"

case "$task" in
  review) verdict_token="REVIEW_VERDICT" ;;
  audit) verdict_token="AUDIT_VERDICT" ;;
  *) echo "unsupported gate task: $task" >&2; exit 2 ;;
esac

plugin_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
claude_bin="${CLAUDE_BIN:-claude}"
permission_mode="${CLAUDE_PERMISSION_MODE:-bypassPermissions}"
model=$(bash "$plugin_root/shared/model_policy.sh" "$task" claude) || exit $?

output=$("$claude_bin" -p "$prompt --worker-model $model" \
  --tools "$allowed_tools" \
  --allowedTools "$allowed_tools" \
  --model "$model" \
  --permission-mode "$permission_mode" \
  --output-format json) || true

result=$(printf '%s' "$output" | python3 "$plugin_root/shared/ci/claude_json.py" result)
echo "$result"
rc=0
printf '%s\n' "$result" | bash "$plugin_root/shared/ci/verdict.sh" "$verdict_token" || rc=$?
printf '%s' "$output" | python3 "$plugin_root/shared/ci/claude_json.py" tokens
exit "$rc"
