from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest


PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY = PLUGIN_ROOT / "shared" / "model_policy.sh"
MODEL_ENV = {
    "CI_TOOLS_REVIEW_MODEL",
    "CI_TOOLS_AUDIT_MODEL",
    "CI_TOOLS_CLAUDE_REVIEW_MODEL",
    "CI_TOOLS_CLAUDE_AUDIT_MODEL",
    "CI_TOOLS_CODEX_REVIEW_MODEL",
    "CI_TOOLS_CODEX_AUDIT_MODEL",
    "CLAUDE_MODEL",
}


def resolve(task: str, provider: str, **values: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if key not in MODEL_ENV}
    env.update(values)
    return subprocess.run(
        ["bash", str(POLICY), task, provider],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class ModelPolicyTests(unittest.TestCase):
    def test_task_defaults_map_per_provider(self) -> None:
        self.assertEqual(resolve("review", "claude").stdout.strip(), "opus")
        self.assertEqual(resolve("audit", "claude").stdout.strip(), "haiku")
        self.assertEqual(resolve("review", "codex").stdout.strip(), "gpt-6-astra")
        self.assertEqual(resolve("audit", "codex").stdout.strip(), "gpt-5.6-luna")

    def test_provider_override_wins(self) -> None:
        result = resolve(
            "review",
            "codex",
            CI_TOOLS_REVIEW_MODEL="fast",
            CI_TOOLS_CODEX_REVIEW_MODEL="gpt-6-astra",
        )
        self.assertEqual(result.stdout.strip(), "gpt-6-astra")

    def test_provider_mismatch_fails_closed(self) -> None:
        result = resolve("review", "codex", CI_TOOLS_REVIEW_MODEL="opus")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a Codex model", result.stderr)

    def test_unsafe_model_fails_closed(self) -> None:
        result = resolve("audit", "claude", CI_TOOLS_AUDIT_MODEL="haiku;echo bad")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid model name", result.stderr)


class CleanupSelectionTests(unittest.TestCase):
    def test_only_marked_notes_by_the_authenticated_bot_are_selected(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "review.py"
        spec = importlib.util.spec_from_file_location("review_helpers", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        discussions = [
            {
                "id": "review",
                "notes": [
                    {
                        "id": 10,
                        "body": "<!-- claude-review:abc -->",
                        "author": {"id": 7},
                    },
                    {
                        "id": 13,
                        "body": "manual follow-up in review thread",
                        "author": {"id": 7},
                    },
                ],
            },
            {
                "id": "human",
                "notes": [
                    {
                        "id": 11,
                        "body": "my own **CRITICAL** note",
                        "author": {"id": 7},
                    }
                ],
            },
            {
                "id": "other",
                "notes": [
                    {
                        "id": 12,
                        "body": "## Automated Code Review",
                        "author": {"id": 8},
                    }
                ],
            },
            {
                "id": "new-inline",
                "notes": [
                    {
                        "id": 14,
                        "body": "<!-- axxx-gitlab-ai -->\n\n🚨 **CRITICAL**: issue",
                        "author": {"id": 7},
                    }
                ],
            },
        ]

        self.assertEqual(
            list(module.iter_review_notes(discussions, 7)),
            [("review", 10), ("new-inline", 14)],
        )

    def test_published_summary_and_inline_notes_have_hidden_markers(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "review.py"
        spec = importlib.util.spec_from_file_location("review_formatters", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        summary = module.format_summary_body("abc123", "Looks good")
        inline = module.format_inline_body("CRITICAL", "Unsafe write")
        self.assertIn("<!-- claude-review:abc123 -->", summary)
        self.assertIn("<!-- axxx-gitlab-ai -->", summary)
        self.assertIn("<!-- axxx-gitlab-ai -->", inline)
        self.assertIn("**CRITICAL**", inline)

    def test_legacy_plugin_marker_remains_cleanup_compatible(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "review.py"
        spec = importlib.util.spec_from_file_location("legacy_marker_rules", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        discussions = [
            {
                "id": "legacy",
                "notes": [
                    {
                        "id": 15,
                        "body": "<!-- axxx-review-audit -->\n\nold plugin output",
                        "author": {"id": 7},
                    }
                ],
            }
        ]
        self.assertEqual(list(module.iter_review_notes(discussions, 7)), [("legacy", 15)])

    def test_plain_headings_and_severity_are_not_cleanup_markers(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "review.py"
        spec = importlib.util.spec_from_file_location("review_marker_rules", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        discussions = [
            {
                "id": "manual",
                "notes": [
                    {
                        "id": 21,
                        "body": "## Automated Code Review\n**CRITICAL**: my note",
                        "author": {"id": 7},
                    }
                ],
            }
        ]
        self.assertEqual(list(module.iter_review_notes(discussions, 7)), [])

    def test_inline_publication_errors_make_the_result_fail(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "review.py"
        spec = importlib.util.spec_from_file_location("review_results", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.summarize_inline_results(
            [
                {"status": "posted"},
                {"status": "skipped"},
                {"status": "error"},
            ]
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["errors"], 1)

    def test_cleanup_deletion_errors_make_the_result_fail(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "review.py"
        spec = importlib.util.spec_from_file_location("cleanup_results", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.summarize_cleanup_result(
            42,
            [10],
            [{"id": 11, "error": "GitLab 500"}],
        )
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["deleted_count"], 1)
        self.assertEqual(len(result["failed"]), 1)


class GitRemoteTests(unittest.TestCase):
    def test_ssh_url_with_port_is_supported(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "git.py"
        spec = importlib.util.spec_from_file_location("git_helpers", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(
            module.parse_remote_url(
                "ssh://git@gitlab.example.com:2222/group/subgroup/repo.git"
            ),
            ("gitlab.example.com", "group/subgroup/repo"),
        )

    def test_no_newline_metadata_does_not_advance_new_side_line(self) -> None:
        module_path = PLUGIN_ROOT / "shared" / "gitlab_ops" / "diff.py"
        spec = importlib.util.spec_from_file_location("diff_helpers", module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        changes = [
            {
                "new_path": "x.py",
                "diff": "@@ -1 +1 @@\n-old\n\\ No newline at end of file\n+new\n\\ No newline at end of file\n",
            }
        ]
        self.assertEqual(module.collect_changed_lines(changes), {"x.py": {1}})


class SkillPolicyTests(unittest.TestCase):
    def test_audit_is_report_only_without_explicit_repair_request(self) -> None:
        text = (PLUGIN_ROOT / "skills" / "audit-agent-config" / "SKILL.md").read_text()
        self.assertIn("Report only by default", text)
        self.assertIn("only when the user explicitly asks", text)

    def test_mutating_review_workflow_requires_explicit_publish_intent(self) -> None:
        shared = (PLUGIN_ROOT / "shared" / "references" / "review-mr.md").read_text()
        self.assertIn("## Authorization gate", shared)
        self.assertIn("Do not delete notes or post anything unless", shared)
        self.assertIn("authorizes only a read-only review", shared)

    def test_pipeline_skill_uses_plugin_shared_helpers(self) -> None:
        skill = PLUGIN_ROOT / "skills" / "repair-pipeline"
        instructions = (skill / "SKILL.md").read_text()
        script = (skill / "scripts" / "fetch_pipeline.py").read_text()
        self.assertIn("<skill-dir>/scripts/fetch_pipeline.py", instructions)
        self.assertIn('parents[3] / "shared"', script)
        self.assertNotIn('pipeline.get("sha", "")[:8]', script)


class CiHelperTests(unittest.TestCase):
    def test_claude_json_result_reaches_verdict_gate(self) -> None:
        parser = PLUGIN_ROOT / "shared" / "ci" / "claude_json.py"
        verdict = PLUGIN_ROOT / "shared" / "ci" / "verdict.sh"
        payload = json.dumps(
            [
                {"type": "result", "result": "Report\n\nREVIEW_VERDICT: PASS"},
            ]
        )
        parsed = subprocess.run(
            ["python3", str(parser), "result"],
            input=payload,
            capture_output=True,
            text=True,
            check=True,
        )
        gated = subprocess.run(
            ["bash", str(verdict), "REVIEW_VERDICT"],
            input=parsed.stdout,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(gated.returncode, 0, gated.stderr)

    def test_missing_verdict_fails_closed(self) -> None:
        verdict = PLUGIN_ROOT / "shared" / "ci" / "verdict.sh"
        gated = subprocess.run(
            ["bash", str(verdict), "AUDIT_VERDICT"],
            input="no decision\n",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(gated.returncode, 1)

    def test_claude_gate_composes_model_result_and_verdict_helpers(self) -> None:
        gate = PLUGIN_ROOT / "shared" / "ci" / "run_claude_gate.sh"
        with tempfile.TemporaryDirectory() as tmp:
            fake = pathlib.Path(tmp) / "claude"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "assert '/gitlab-ai:audit-agent-config check --worker-model haiku' in sys.argv\n"
                "assert '--tools' in sys.argv and 'Read,Skill' in sys.argv\n"
                "print(json.dumps({'type':'result','result':os.environ['FAKE_RESULT'],"
                "'usage':{'input_tokens':1,'output_tokens':2}}))\n"
            )
            fake.chmod(0o755)
            env = {key: value for key, value in os.environ.items() if key not in MODEL_ENV}
            env.update(
                CLAUDE_BIN=str(fake),
                FAKE_RESULT="AUDIT_VERDICT: PASS",
            )
            result = subprocess.run(
                [
                    "bash",
                    str(gate),
                    "audit",
                    "/gitlab-ai:audit-agent-config check",
                    "Read,Skill",
                ],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AUDIT_VERDICT: PASS", result.stdout)
        self.assertIn("Tokens", result.stdout)


if __name__ == "__main__":
    unittest.main()
