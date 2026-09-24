from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
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
                        "body": "<!-- axxx-review-audit -->\n\n🚨 **CRITICAL**: issue",
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
        self.assertIn("<!-- axxx-review-audit -->", summary)
        self.assertIn("<!-- axxx-review-audit -->", inline)
        self.assertIn("**CRITICAL**", inline)

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


class SkillPolicyTests(unittest.TestCase):
    def test_audit_is_report_only_without_explicit_repair_request(self) -> None:
        text = (PLUGIN_ROOT / "skills" / "agent-config-audit" / "SKILL.md").read_text()
        self.assertIn("Report only by default", text)
        self.assertIn("only when the user explicitly asks", text)

    def test_mutating_review_workflow_requires_explicit_publish_intent(self) -> None:
        shared = (PLUGIN_ROOT / "shared" / "references" / "review-mr.md").read_text()
        self.assertIn("## Authorization gate", shared)
        self.assertIn("Do not delete notes or post anything unless", shared)
        self.assertIn("authorizes only a read-only review", shared)


if __name__ == "__main__":
    unittest.main()
