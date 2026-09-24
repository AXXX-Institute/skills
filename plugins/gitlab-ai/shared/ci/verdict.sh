#!/usr/bin/env bash
# Decide a claude CI job's pass/fail from its verdict line.
#
# Usage:  printf '%s\n' "$output" | verdict.sh <TOKEN>
#   TOKEN is the verdict prefix, e.g. AUDIT_VERDICT or REVIEW_VERDICT.
#
# Reads the job's full output on stdin and extracts the verdict token. It
# tolerates the model wrapping the line in markdown (e.g. **AUDIT_VERDICT:
# PASS** or AUDIT_VERDICT: **PASS**) and uses the LAST decision, so a prose
# mention earlier in the report can't decide the gate. Prints the resolved
# verdict and exits:
#   0  — verdict is PASS
#   1  — verdict is FAIL, or no verdict token was found at all
#
# Two rules keep prose out of the gate, both learned from real jobs:
#
#   1. The verdict must OPEN its line (modulo markdown/quote decoration). A
#      sentence that merely mentions the token mid-line is not a verdict.
#   2. The word must be a decision, not the skill's own "PASS|FAIL" template
#      quoted back. agentic-rag's auto-review once ran in plan mode and
#      described what it WOULD do — "Ends with a `REVIEW_VERDICT: PASS|FAIL`
#      line" — which the old grep read as PASS. A job that reviewed nothing
#      gated green, which is worse than the red it replaced.
#
# `|| true` guards the pipeline so a no-match never aborts the caller under
# `set -o pipefail`; a missing verdict is then handled explicitly as a failure.
set -uo pipefail

token="${1:?usage: verdict.sh <TOKEN> (output on stdin)}"

# Rule 1 is the first grep (line must open with the token), rule 2 the second
# (the decision must not be followed by "|"). A line that opens with the token
# but carries no decision yields nothing, so an earlier real verdict still wins.
verdict=$(grep -E "^[[:space:]>*_\`-]*${token}:" \
          | grep -Eo "${token}:[[:space:]*_\`]*(PASS|FAIL)([^[:alnum:]_|]|$)" \
          | grep -Eo '(PASS|FAIL)' | tail -1 || true)

if [ -z "$verdict" ]; then
  echo "✗ No ${token} line found in the job output." >&2
  echo "  It must open its own line, e.g. '${token}: PASS'." >&2
  exit 1
fi

echo "${token}: ${verdict}"
[ "$verdict" = "FAIL" ] && exit 1
exit 0
