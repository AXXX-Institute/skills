#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Helpers for a `claude -p --output-format json` run, used by the CI gates.

Reads claude's JSON output on stdin, in EITHER shape the CLI emits: a single
result object, or (claude 2.1.x) an ARRAY of session events whose last
``{"type": "result"}`` entry carries the text and usage. Handling only the
object shape looked harmless — `result` fell through to passing the raw JSON
along — but it meant the gate grepped the whole event log, where the verdict
sits mid-line inside an escaped "\\n", and the token line always read
"unavailable". Depending on the mode arg:

  result   print the assistant's final result text (fed to the verdict gate and
           echoed into the job log). Passes input through unchanged if it isn't
           the expected JSON (e.g. claude errored), so the gate can still decide.
  tokens   print a one-line token-usage summary for the session (input/output/
           cache tokens + cost). Printed at the end of the job.

Stdlib only (json) — no third-party deps. Always exits 0; the verdict gate
(`verdict.sh`) owns pass/fail. Installed-plugin consumers run it from
`<plugin-dir>/shared/ci/claude_json.py <mode>`.
"""

from __future__ import annotations

import json
import sys


def _load(raw: str) -> dict | None:
    """Return the result object, from either output shape.

    A single object is used as-is. An array of session events is searched from
    the END for the terminal ``{"type": "result"}`` entry — from the end because
    a subagent's own result event can appear earlier in the same stream, and the
    session's verdict is the last one.
    """
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        for item in reversed(data):
            if isinstance(item, dict) and item.get("type") == "result":
                return item
        # No typed result event (older/partial streams): settle for the last
        # entry that carries a session-level result or usage.
        for item in reversed(data):
            if isinstance(item, dict) and ("result" in item or "usage" in item):
                return item
    return None


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "result"
    raw = sys.stdin.read()
    data = _load(raw)

    if mode == "result":
        result = data.get("result") if data else None
        sys.stdout.write(result if isinstance(result, str) else raw)
        return

    if mode == "tokens":
        usage = (data or {}).get("usage") or {}

        def n(key: str) -> int:
            val = usage.get(key, 0)
            return val if isinstance(val, int) else 0

        inp, out = n("input_tokens"), n("output_tokens")
        cache_create = n("cache_creation_input_tokens")
        cache_read = n("cache_read_input_tokens")
        total = inp + out + cache_create + cache_read
        if data is None or not usage:
            print("📊 Tokens — unavailable (claude output was not JSON usage)")
            return
        line = (
            f"📊 Tokens — input {inp}, output {out}, "
            f"cache_create {cache_create}, cache_read {cache_read}, total {total}"
        )
        cost = data.get("total_cost_usd")
        if isinstance(cost, (int, float)):
            line += f" | cost ${cost:.4f}"
        print(line)
        return

    print(f"unknown mode: {mode}", file=sys.stderr)


if __name__ == "__main__":
    main()
