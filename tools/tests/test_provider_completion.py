"""Offline regressions for the CLI envelope surrounding a review contract.

Grok envelope fields follow the upstream headless protocol documentation; these
are synthetic payloads, not replayed provider reviews. No model is invoked.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools import external_review as bridge
from tools.tests.test_external_review import (
    HEAD, PR_NUMBER, FakeAdapter, FakeGitHub, FakeRepository, execution, metadata,
)


def contract():
    return {
        "pr_number": PR_NUMBER, "head_sha": HEAD, "verdict": "PASS",
        "body_markdown": "No material findings.", "findings": [],
    }


class ProviderCompletionTests(unittest.TestCase):
    def test_interrupted_cli_cannot_publish_a_valid_looking_pass(self):
        for provider in ("Claude", "Grok"):
            for field in ("stopReason", "stop_reason"):
                for reason in ("max_tokens", "max_turn_requests", "refusal", "cancelled", "tool_use", "pause_turn"):
                    with self.subTest(provider=provider, field=field, reason=reason):
                        payload = {field: reason, "structured_output": contract()}
                        with self.assertRaisesRegex(bridge.ReviewBridgeError, reason):
                            bridge.extract_contract(json.dumps(payload), provider)

    def test_error_metadata_overrides_all_payload_fallbacks(self):
        errors = (
            {"is_error": True}, {"is_error": "false"}, {"is_error": None},
            {"type": "error"}, {"subtype": "error_max_turns"},
            {"error": {"message": "private prompt echo"}},
            {"structured_output_error": "private schema echo"},
            {"structuredOutputError": "private schema echo"},
        )
        for provider in ("Claude", "Grok"):
            for failure in errors:
                with self.subTest(provider=provider, failure=failure):
                    payload = {
                        "structured_output": contract(), "structuredOutput": contract(),
                        "text": json.dumps(contract()), "result": json.dumps(contract()),
                        "stopReason": "end_turn", **failure,
                    }
                    with self.assertRaises(bridge.ReviewBridgeError) as caught:
                        bridge.extract_contract(json.dumps(payload), provider)
                    self.assertNotIn("private", str(caught.exception))

    def test_malformed_or_conflicting_stop_metadata_is_rejected_without_echo(self):
        for reason in (True, 0, [], {}, "private prompt echo"):
            with self.subTest(reason=reason):
                payload = {"stopReason": reason, "structuredOutput": contract()}
                with self.assertRaisesRegex(bridge.ReviewBridgeError, "unrecognized") as caught:
                    bridge.extract_contract(json.dumps(payload), "Grok")
                self.assertNotIn("private", str(caught.exception))
        payload = {"stopReason": "end_turn", "stop_reason": "max_tokens", "structuredOutput": contract()}
        with self.assertRaises(bridge.ReviewBridgeError):
            bridge.extract_contract(json.dumps(payload), "Grok")

    def test_completed_structured_review_wins_over_progress_text(self):
        for key in ("structured_output", "structuredOutput"):
            payload = {
                "stopReason": "end_turn", key: contract(),
                "text": "Inspection started; final review follows after reading files.",
                "modelUsage": {"grok-4.6": {"modelCalls": 3}},
                "num_turns": 3,
            }
            parsed, model = bridge.extract_contract(json.dumps(payload), "Grok")
            self.assertEqual(parsed, contract())
            self.assertEqual(model, "grok-4.6")

    def test_success_metadata_and_legacy_contracts_remain_supported(self):
        for payload in (
            contract(),
            {"structured_output": contract()},
            {"type": "result", "subtype": "success", "is_error": False,
             "stop_reason": "end_turn", "structured_output": contract()},
            {"stopReason": "end_turn", "text": json.dumps(contract())},
            {"type": "result", "subtype": "success", "is_error": False,
             "stop_reason": None, "structured_output": contract()},
        ):
            with self.subTest(payload=payload):
                parsed, _ = bridge.extract_contract(json.dumps(payload), "Claude")
                self.assertEqual(parsed, contract())

    def test_interrupted_grok_retains_claude_without_posting(self):
        class InterruptedAdapter:
            def run(self, worktree, prompt):
                bridge.extract_contract(json.dumps({
                    "stopReason": "max_tokens", "structured_output": contract(),
                }), "Grok")
                raise AssertionError("interrupted review must not reach publication")

        github = FakeGitHub([metadata()])
        repository = FakeRepository()
        with tempfile.TemporaryDirectory() as temp:
            state_dir = Path(temp) / "reviews"
            with self.assertRaisesRegex(bridge.ReviewBridgeError, "max_tokens"):
                bridge.ReviewBridge(github, repository, {
                    "claude": FakeAdapter(execution("claude")),
                    "grok": InterruptedAdapter(),
                }, emit=lambda _: None).review(
                    PR_NUMBER, ("claude", "grok"), "Review the diff.", state_dir=state_dir,
                )
            state = json.loads(next(state_dir.glob("*.json")).read_text())
            self.assertEqual(state["providers"]["claude"]["status"], "validated")
            self.assertEqual(state["providers"]["grok"]["status"], "failed")
        self.assertEqual(github.comments, [])
        self.assertTrue(repository.cleaned)


if __name__ == "__main__":
    unittest.main()
