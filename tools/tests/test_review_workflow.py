from __future__ import annotations

from dataclasses import replace
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import external_review as bridge
from tools.review_state import ReviewState, StateError
from tools.tests.test_external_review import (
    BASE, HEAD, MOVED_HEAD, PR_NUMBER, FakeAdapter, FakeGitHub, FakeRepository,
    execution, metadata,
)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "reviews"
        self.prompt = "Inspect the complete diff."

    def invoke(self, outcomes=None, *, resume=None, collect=False, github=None,
               repository=None, prompt=None, providers=("claude", "grok")):
        adapters = {name: FakeAdapter(value) for name, value in (outcomes or {
            "claude": execution("claude"), "grok": execution("grok")}).items()}
        self.adapters = adapters
        self.github = github or FakeGitHub([metadata(), metadata()])
        self.repository = repository or FakeRepository()
        return bridge.ReviewBridge(self.github, self.repository, adapters, emit=lambda _: None).review(
            PR_NUMBER, providers, self.prompt if prompt is None else prompt,
            state_dir=self.directory, resume=resume, collect_only=collect,
        )

    def checkpoint(self):
        paths = list(self.directory.glob("*.json"))
        self.assertEqual(len(paths), 1)
        return paths[0]

    def test_failed_provider_does_not_discard_success_and_resume_only_reruns_failure(self):
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "posted reviews: none"):
            self.invoke({"claude": bridge.ReviewBridgeError("temporary outage"), "grok": execution("grok")})
        self.assertEqual(len(self.adapters["grok"].prompts), 1)
        self.assertEqual(self.github.comments, [])
        path = self.checkpoint()
        data = json.loads(path.read_text())
        self.assertEqual(data["providers"]["grok"]["status"], "validated")
        self.assertEqual(data["providers"]["claude"]["status"], "failed")
        posted = self.invoke({"claude": execution("claude"), "grok": AssertionError("must reuse")}, resume=path)
        self.assertEqual(len(posted), 2)
        self.assertEqual(len(self.adapters["claude"].prompts), 1)
        self.assertEqual(self.adapters["grok"].prompts, [])
        self.assertEqual(self.repository.symlink_checks, 1)

    def test_each_live_provider_has_an_independent_clean_checkout(self):
        self.invoke()
        self.assertEqual(self.repository.symlink_checks, 2)
        self.assertEqual(self.repository.clean_checks, ["Claude", "Grok"])
        self.assertTrue(self.repository.cleaned)

    def test_dirty_provider_cannot_poison_second_provider_or_be_retained(self):
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "dirty-worktree"):
            self.invoke(repository=FakeRepository(clean_error_for="Claude"))
        self.assertEqual(len(self.adapters["grok"].prompts), 1)
        data = json.loads(self.checkpoint().read_text())
        self.assertEqual(data["providers"]["claude"]["status"], "failed")
        self.assertNotIn("execution", data["providers"]["claude"])
        self.assertEqual(self.github.comments, [])

    def test_collection_can_be_resumed_for_posting_without_another_model_call(self):
        self.assertEqual(self.invoke(collect=True), [])
        self.assertEqual(self.github.comments, [])
        path = self.checkpoint()
        posted = self.invoke({"claude": AssertionError("must reuse"), "grok": AssertionError("must reuse")}, resume=path)
        self.assertEqual(len(posted), 2)
        self.assertEqual(self.repository.symlink_checks, 0)
        self.assertTrue(all(not adapter.prompts for adapter in self.adapters.values()))
        self.assertEqual(len(self.github.comments), 2)

    def test_completed_checkpoint_does_not_duplicate_comments(self):
        first = self.invoke()
        repeated = self.invoke(resume=self.checkpoint())
        self.assertEqual(repeated, first)
        self.assertEqual(self.github.comments, [])
        self.assertTrue(all(not adapter.prompts for adapter in self.adapters.values()))

    def test_fresh_invocation_does_not_implicitly_replay_prior_results(self):
        self.invoke(collect=True)
        self.invoke(collect=True)
        self.assertEqual(len(list(self.directory.glob("*.json"))), 2)
        self.assertTrue(all(len(adapter.prompts) == 1 for adapter in self.adapters.values()))

    def test_mismatched_prompt_or_provider_selection_blocks_resume_before_models(self):
        self.invoke(collect=True)
        path = self.checkpoint()
        for options in ({"prompt": "Different scope"}, {"providers": ("grok",)}):
            with self.subTest(options=options), self.assertRaisesRegex(bridge.ReviewAttemptError, "resume identity differs"):
                self.invoke(resume=path, **options)
            self.assertTrue(all(not adapter.prompts for adapter in self.adapters.values()))
            self.assertEqual(self.github.comments, [])

    def test_changed_head_base_or_bridge_blocks_retained_evidence(self):
        self.invoke(collect=True)
        path = self.checkpoint()
        for field, value in (("head_sha", MOVED_HEAD), ("base_sha", "b" * 40), ("base_ref", "other-base"), ("url", "https://other.example/pr/104")):
            changed = replace(metadata(), **{field: value})
            repo = FakeRepository()
            repo.base_to_head_diff = lambda _base, _head: "diff --git a/tool.py b/tool.py\n"
            with self.subTest(field=field), self.assertRaisesRegex(bridge.ReviewAttemptError, "resume identity differs"):
                self.invoke(resume=path, github=FakeGitHub([changed]), repository=repo)
            self.assertTrue(all(not adapter.prompts for adapter in self.adapters.values()))
        original = bridge.review_identity
        def changed_bridge(*args):
            return {**original(*args), "bridge_sha256": "different implementation"}
        with mock.patch.object(bridge, "review_identity", side_effect=changed_bridge), self.assertRaisesRegex(bridge.ReviewAttemptError, "resume identity differs"):
            self.invoke(resume=path)

    def test_live_base_change_blocks_posting_after_collection(self):
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "base changed"):
            self.invoke(github=FakeGitHub([metadata(), replace(metadata(), base_sha="b" * 40)]))
        self.assertEqual(self.github.comments, [])

    def test_retained_result_is_revalidated_not_trusted_as_arbitrary_json(self):
        self.invoke(collect=True)
        path = self.checkpoint()
        data = json.loads(path.read_text())
        data["providers"]["grok"]["execution"]["result"]["head_sha"] = MOVED_HEAD
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "returned head"):
            self.invoke(resume=path)
        self.assertEqual(self.github.comments, [])
        self.assertTrue(all(not adapter.prompts for adapter in self.adapters.values()))

    def test_uncertain_posting_is_checkpointed_and_never_automatically_repeated(self):
        class InterruptedPost(FakeGitHub):
            def post_comment(self, *args):
                super().post_comment(*args)
                raise bridge.ReviewBridgeError("connection lost after submission")
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "outcome may be uncertain"):
            self.invoke(github=InterruptedPost([metadata(), metadata()]))
        path = self.checkpoint()
        self.assertEqual(json.loads(path.read_text())["providers"]["claude"]["status"], "posting")
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "automatic reposting is blocked"):
            self.invoke(resume=path)
        self.assertEqual(self.github.comments, [])
        self.assertTrue(all(not adapter.prompts for adapter in self.adapters.values()))

    def test_interrupt_retains_completed_provider_and_reruns_only_interrupted_one(self):
        class InterruptAdapter(FakeAdapter):
            def run(self, *_args):
                raise KeyboardInterrupt()
        adapters = {"claude": FakeAdapter(execution("claude")), "grok": InterruptAdapter(None)}
        with self.assertRaises(KeyboardInterrupt):
            bridge.ReviewBridge(FakeGitHub([metadata()]), FakeRepository(), adapters, emit=lambda _:None).review(
                PR_NUMBER, ("claude", "grok"), self.prompt, state_dir=self.directory)
        self.invoke(resume=self.checkpoint())
        self.assertEqual(self.adapters["claude"].prompts, [])
        self.assertEqual(len(self.adapters["grok"].prompts), 1)

    def test_nonfinal_diagnostic_identifies_field_without_retaining_raw_rejected_review(self):
        raw = execution("claude", verdict="FINDINGS", body="private raw body", findings=(
            bridge.ReviewFinding("LOW", "placeholder", "private raw finding"),))
        with self.assertRaisesRegex(bridge.ReviewAttemptError, r"findings\[0\].title: placeholder field"):
            self.invoke({"claude": raw, "grok": execution("grok")})
        checkpoint = self.checkpoint().read_text()
        self.assertNotIn("private raw body", checkpoint)
        self.assertNotIn("private raw finding", checkpoint)
        self.assertNotIn(self.prompt, checkpoint)

    def test_cli_collect_and_resume_use_checkpoints_without_live_services(self):
        prompt_file = Path(self.temporary.name) / "request.md"
        prompt_file.write_text(self.prompt)
        arguments = ["review", "--pr", str(PR_NUMBER), "--provider", "all", "--prompt-file", str(prompt_file),
                     "--state-dir", str(self.directory), "--expected-head", HEAD]
        first = FakeGitHub([metadata(), metadata()])
        with mock.patch.object(bridge, "GitHubClient", return_value=first), \
             mock.patch.object(bridge, "GitRepository", return_value=FakeRepository()), \
             mock.patch.object(bridge, "ProviderAdapter", side_effect=lambda spec, _runner: FakeAdapter(execution(spec.key))), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bridge.main([*arguments, "--collect-only"]), 0)
        self.assertEqual(first.comments, [])
        second = FakeGitHub([metadata(), metadata()])
        adapters = {name: FakeAdapter(AssertionError("cached provider must not run")) for name in ("claude", "grok")}
        with mock.patch.object(bridge, "GitHubClient", return_value=second), \
             mock.patch.object(bridge, "GitRepository", return_value=FakeRepository()), \
             mock.patch.object(bridge, "ProviderAdapter", side_effect=lambda spec, _runner: adapters[spec.key]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bridge.main([*arguments, "--resume", str(self.checkpoint())]), 0)
        self.assertEqual(len(second.comments), 2)
        self.assertTrue(all(not adapter.prompts for adapter in adapters.values()))

    def test_checkpointed_reviews_and_incomplete_diagnostics_redact_secrets(self):
        secret = "ghp_privatevalue12345678"
        with self.assertRaises(bridge.ReviewAttemptError) as caught:
            self.invoke({
                "claude": execution("claude", verdict="INCOMPLETE", body=f"Authentication failed api_key={secret}"),
                "grok": execution("grok", body=f"No material findings. Token example: {secret}"),
            })
        self.assertNotIn(secret, str(caught.exception))
        self.assertNotIn(secret, self.checkpoint().read_text())
        self.assertIn("[REDACTED]", self.checkpoint().read_text())

    def test_real_git_checkouts_are_isolated_cleaned_and_resumable(self):
        root = Path(self.temporary.name)
        checkout = root / "repository"
        checkout.mkdir()
        def git(*args):
            return subprocess.run(
                ("git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgSign=false",
                 "-c", "user.name=Review Test", "-c", "user.email=review@example.invalid", *args),
                cwd=checkout, check=True, capture_output=True, text=True,
            ).stdout.strip()
        git("init", "--template=", "--initial-branch=main")
        (checkout / "example.txt").write_text("base\n")
        git("add", "example.txt")
        git("commit", "-m", "base")
        base = git("rev-parse", "HEAD")
        (checkout / "example.txt").write_text("head\n")
        git("commit", "-am", "head")
        head = git("rev-parse", "HEAD")
        actual_metadata = replace(metadata(), head_sha=head, base_sha=base)
        repository = bridge.GitRepository(bridge.SubprocessRunner(), checkout, temporary_parent=root / "isolated")
        paths = []
        outer = self
        class ReadingAdapter:
            def __init__(self, name, dirty=False):
                self.name, self.dirty = name, dirty
                self.calls = 0
            def run(self, worktree, prompt):
                self.calls += 1
                paths.append(worktree)
                outer.assertEqual((worktree / "example.txt").read_text(), "head\n")
                outer.assertIn("+head", prompt)
                if self.dirty:
                    (worktree / "example.txt").write_text("contamination\n")
                value = execution(self.name)
                return replace(value, result=replace(value.result, head_sha=head))
        adapters = {"claude": ReadingAdapter("claude", dirty=True), "grok": ReadingAdapter("grok")}
        first = FakeGitHub([actual_metadata])
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "modified the detached review worktree"):
            bridge.ReviewBridge(first, repository, adapters, emit=lambda _:None).review(
                PR_NUMBER, ("claude", "grok"), self.prompt, state_dir=self.directory)
        self.assertEqual(first.comments, [])
        self.assertEqual(len(set(paths)), 2)
        self.assertTrue(all(not path.exists() for path in paths))
        self.assertEqual(git("status", "--porcelain"), "")
        adapters["claude"] = ReadingAdapter("claude")
        second = FakeGitHub([actual_metadata, actual_metadata])
        posted = bridge.ReviewBridge(second, repository, adapters, emit=lambda _:None).review(
            PR_NUMBER, ("claude", "grok"), self.prompt, state_dir=self.directory, resume=self.checkpoint())
        self.assertEqual(len(posted), 2)
        self.assertEqual(adapters["grok"].calls, 1)
        self.assertTrue(all(not path.exists() for path in paths))
        self.assertEqual(git("worktree", "list", "--porcelain").count("worktree "), 1)

    def test_ci_head_handoff_cannot_review_a_new_unchecked_head(self):
        adapters = {"claude": FakeAdapter(execution("claude"))}
        github = FakeGitHub([metadata()])
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "CI-validated expected head"):
            bridge.ReviewBridge(github, FakeRepository(), adapters, emit=lambda _: None).review(
                PR_NUMBER, ("claude",), self.prompt, expected_head=MOVED_HEAD)
        self.assertEqual(adapters["claude"].prompts, [])
        self.assertEqual(github.comments, [])

    def test_partial_posting_receipt_survives_second_provider_network_failure(self):
        class SecondPostFails(FakeGitHub):
            def post_comment(self, *args):
                if self.comments:
                    raise bridge.ReviewBridgeError("network timeout")
                return super().post_comment(*args)
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "1 confirmed comments"):
            self.invoke(github=SecondPostFails([metadata(), metadata()]))
        path = self.checkpoint()
        states = json.loads(path.read_text())["providers"]
        self.assertEqual(states["claude"]["status"], "posted")
        self.assertEqual(states["grok"]["status"], "posting")
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "automatic reposting is blocked"):
            self.invoke(resume=path)
        self.assertEqual(self.github.comments, [])

    def test_incomplete_is_an_explicit_nonpublishable_outcome(self):
        payload = {"pr_number": PR_NUMBER, "head_sha": HEAD, "verdict": "INCOMPLETE",
                   "body_markdown": "Cannot read repository files.", "findings": []}
        result = bridge.review_result_from_contract(payload)
        with self.assertRaisesRegex(bridge.ReviewAttemptError, "INCOMPLETE.*Cannot read repository"):
            self.invoke({"claude": replace(execution("claude"), result=result), "grok": execution("grok")})
        self.assertEqual(self.github.comments, [])
        self.assertEqual(len(self.adapters["grok"].prompts), 1)


class CaptureTests(unittest.TestCase):
    def test_cli_output_uses_regular_files_and_preserves_large_stdout_and_stderr(self):
        script = "import os,stat; print(stat.S_ISREG(os.fstat(1).st_mode)); os.write(1,b'x'*70000); os.write(2,b'y'*70000)"
        result = bridge.SubprocessRunner().run((sys.executable, "-c", script), timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("True", result.stdout)
        self.assertEqual(result.stdout.count("x"), 70000)
        self.assertEqual(result.stderr, "y" * 70000)

    def test_prompt_diff_markers_do_not_destroy_flags_or_failure_diagnostics(self):
        prompt = "private first line\n-\n+\n{}\n---\n \nprivate second line"
        message = "Claude lacks --permission-mode; base-to-head check failed"
        result = bridge.diagnostic_text(message + " private first line", bridge.prompt_redactions(prompt))
        self.assertIn(message, result)
        self.assertNotIn("private first line", result)
        self.assertIn("[REDACTED]", result)
        # Explicit secrets remain redactions even if they consist of punctuation.
        self.assertEqual(bridge.diagnostic_text("password !!!", ("!!!",)), "password [REDACTED]")


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "private"
        self.identity = {"head": HEAD, "base": BASE, "prompt": "hash"}

    def test_private_permissions_and_exclusive_resume_lock(self):
        with ReviewState.open(self.directory, self.identity) as state:
            self.assertEqual(self.directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual(state.path.stat().st_mode & 0o777, 0o600)
            with self.assertRaisesRegex(StateError, "already running"):
                with ReviewState.open(self.directory, self.identity, state.path):
                    self.fail("concurrent attempt acquired lock")
        with ReviewState.open(self.directory, self.identity, state.path) as resumed:
            self.assertEqual(resumed.data, state.data)

    def test_symlink_or_public_resume_file_is_rejected_without_following_it(self):
        with ReviewState.open(self.directory, self.identity) as state:
            path = state.path
        public = self.directory / "alias.json"
        public.symlink_to(path)
        with self.assertRaises(StateError):
            with ReviewState.open(self.directory, self.identity, public):
                self.fail("followed a symlink")
        path.chmod(0o644)
        with self.assertRaisesRegex(StateError, "private regular file"):
            with ReviewState.open(self.directory, self.identity, path):
                self.fail("read a public checkpoint")

    def test_malformed_checkpoint_does_not_expose_contents(self):
        with ReviewState.open(self.directory, self.identity) as state:
            path = state.path
        path.write_text("private malformed contents")
        with self.assertRaises(StateError) as caught:
            with ReviewState.open(self.directory, self.identity, path):
                self.fail("read malformed checkpoint")
        self.assertNotIn("private malformed contents", str(caught.exception))

    def test_failed_atomic_replace_preserves_previous_checkpoint(self):
        with ReviewState.open(self.directory, self.identity) as state:
            previous = state.path.read_bytes()
            with mock.patch("tools.review_state.os.replace", side_effect=OSError("disk failure")), self.assertRaises(OSError):
                state.record("claude", "running")
            self.assertEqual(state.path.read_bytes(), previous)
            self.assertEqual(list(self.directory.glob(".review-*")), [])


if __name__ == "__main__":
    unittest.main()
