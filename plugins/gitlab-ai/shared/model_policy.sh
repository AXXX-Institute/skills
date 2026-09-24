#!/usr/bin/env bash
# Resolve the model for one ci-tools specialist role.
#
# Usage: model_policy.sh <review|audit> <claude|codex>
#
# Precedence:
#   CI_TOOLS_<PROVIDER>_<TASK>_MODEL
#   CI_TOOLS_<TASK>_MODEL
#   CLAUDE_MODEL (legacy, Claude only)
#   role default (review=high, audit=fast)
set -euo pipefail

task=${1:-}
provider=${2:-}
case "$task" in review|audit) ;; *) echo "ERROR: task must be review or audit" >&2; exit 2 ;; esac
case "$provider" in claude|codex) ;; *) echo "ERROR: provider must be claude or codex" >&2; exit 2 ;; esac

task_upper=${task^^}
provider_upper=${provider^^}
provider_var="CI_TOOLS_${provider_upper}_${task_upper}_MODEL"
task_var="CI_TOOLS_${task_upper}_MODEL"
model=${!provider_var:-}
[ -n "$model" ] || model=${!task_var:-}
[ -n "$model" ] || { [ "$provider" = claude ] && model=${CLAUDE_MODEL:-}; }
[ -n "$model" ] || { [ "$task" = review ] && model=high || model=fast; }

case "$provider:$model" in
  claude:high) model=opus ;;
  claude:fast) model=haiku ;;
  codex:high) model=gpt-6-astra ;;
  codex:fast) model=gpt-5.6-luna ;;
  codex:gpt-*|codex:astra|codex:sol|codex:terra|codex:luna) ;;
  codex:*)
    echo "ERROR: '$model' is not a Codex model or logical tier (high/fast)" >&2
    exit 2
    ;;
  claude:gpt-*|claude:astra|claude:sol|claude:terra|claude:luna)
    echo "ERROR: '$model' is not a Claude model or logical tier (high/fast)" >&2
    exit 2
    ;;
esac

case "$model" in
  *[!A-Za-z0-9._:/-]*|'')
    echo "ERROR: invalid model name '$model'" >&2
    exit 2
    ;;
esac
printf '%s\n' "$model"
