"""Verify workflow evidence in temporary directories without Git writes."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "factory.py"
SPEC = importlib.util.spec_from_file_location("factory", SCRIPT)
factory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(factory)


class FactoryFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "source"
        self.root.mkdir()
        self.repo = self.root.parent / "original"
        self.repo.mkdir()
        self.job = Path(str(self.root) + ".factory")
        self.job.mkdir()
        self.branch = "feat/example"
        self.head = "a" * 40
        self.staged = ""
        self.common = str(self.repo / ".git")
        self.calls = []
        self.state = {
            "schema": factory.SCHEMA, "repo": str(self.repo), "worktree": str(self.root),
            "branch": self.branch, "base_ref": "refs/heads/main", "base_commit": self.head,
            "stage": "baseline", "repairs": 0, "check_count": 0, "reviewers": [],
            "reviews": {}, "last_check": None, "baseline_config": None,
            "baseline_tree": None, "reason": None,
        }
        (self.root / "source.txt").write_text("original\n", encoding="utf-8")
        (self.job / "request.md").write_text("Change the greeting.\n", encoding="utf-8")
        self.set_checks("pass")
        factory.save(self.job, self.state)
        self.git_mock = patch.object(factory, "read_git", side_effect=self.read_git)
        self.git_mock.start()
        self.addCleanup(self.git_mock.stop)

    def read_git(self, root, *args):
        self.calls.append((Path(root), args))
        if args == ("rev-parse", "--show-toplevel"):
            return str(root) + "\n"
        if args == ("rev-parse", "--path-format=absolute", "--git-common-dir"):
            return self.common + "\n"
        if args == ("symbolic-ref", "--quiet", "--short", "HEAD"):
            return self.branch + "\n"
        if args == ("rev-parse", "HEAD"):
            return self.head + "\n"
        if args[0] == "diff":
            return self.staged
        if args[0] == "ls-files":
            names = [str(path.relative_to(root)) for path in Path(root).rglob("*")
                     if path.is_file() or path.is_symlink()]
            return "\0".join(names) + "\0"
        if args[0] == "check-ref-format":
            return args[-1] + "\n"
        if args[0] == "rev-parse" and "--verify" in args:
            if args[-1] == "refs/heads/main^{commit}":
                return self.head + "\n"
            raise factory.Refusal("Unknown local ref.")
        raise AssertionError("Unexpected Git query: " + repr(args))

    def set_checks(self, behavior):
        program = {
            "pass": "print('passed')",
            "fail": "import sys; print('failed'); sys.exit(1)",
            "mutate": "from pathlib import Path; Path('source.txt').write_text('changed')",
            "timeout": "import time; time.sleep(10)",
        }[behavior]
        checks = [{"name": "tests", "argv": [sys.executable, "-c", program],
                   "timeout": 0.02 if behavior == "timeout" else 30}]
        (self.job / "checks.json").write_text(json.dumps(checks), encoding="utf-8")

    def check(self, resolved=False):
        return factory.run_checks(self.job, argparse.Namespace(resolved=resolved))

    def build(self, reviewers=("code",)):
        state, code = self.check()
        self.assertEqual(code, 0)
        (self.job / "plan.md").write_text("Change greeting and test it.\n", encoding="utf-8")
        return factory.start_build(self.job, argparse.Namespace(reviewers=reviewers))

    def review(self, role="code", result="pass", check_id=None, snapshot=None):
        state = factory.load(self.job)
        evidence = state["last_check"]
        report = self.job / ("input-" + role + ".md")
        report.write_text("Checked the greeting and its callers.\n", encoding="utf-8")
        return factory.record_review(self.job, argparse.Namespace(
            role=role, result=result, mode="separate", report_file=str(report),
            check_id=evidence["id"] if check_id is None else check_id,
            snapshot=evidence["snapshot"] if snapshot is None else snapshot,
        ))


class JobCase(FactoryFixture):
    def test_successful_job_keeps_source_uncommitted(self):
        self.build()
        (self.root / "source.txt").write_text("new greeting\n", encoding="utf-8")
        state, code = self.check()
        self.assertEqual((code, state["stage"]), (0, "review"))
        self.assertEqual(self.review()["stage"], "ready")
        self.assertTrue(factory.status(self.job)["can_handoff"])
        self.assertEqual((self.root / "source.txt").read_text(), "new greeting\n")
        self.assertTrue(all(args[0] in factory.READ_COMMANDS for _, args in self.calls))

    def test_baseline_failure_requires_user_resolution(self):
        self.set_checks("fail")
        state, code = self.check()
        self.assertEqual((code, state["stage"], state["repairs"]), (1, "baseline-blocked", 0))
        with self.assertRaisesRegex(factory.Refusal, "resolve baseline"):
            self.check()
        self.set_checks("pass")
        state, code = self.check(resolved=True)
        self.assertEqual((code, state["stage"]), (0, "plan"))

    def test_no_checks_cannot_pass_baseline(self):
        (self.job / "checks.json").write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(factory.Refusal, "required checks"):
            self.check()

    def test_check_timeout_is_baseline_failure(self):
        self.set_checks("timeout")
        state, code = self.check()
        self.assertEqual((code, state["stage"]), (1, "baseline-blocked"))
        self.assertEqual(state["last_check"]["results"][0]["error"], "Timeout expired.")

    def test_unavailable_check_is_baseline_failure(self):
        config = [{"name": "missing", "argv": [str(self.root / "unavailable-command")]}]
        (self.job / "checks.json").write_text(json.dumps(config), encoding="utf-8")
        state, code = self.check()
        self.assertEqual((code, state["stage"]), (1, "baseline-blocked"))
        self.assertIsNotNone(state["last_check"]["results"][0]["error"])

    def test_check_that_edits_source_does_not_pass(self):
        self.set_checks("mutate")
        state, code = self.check()
        self.assertEqual((code, state["stage"]), (1, "baseline-blocked"))
        self.assertFalse(state["last_check"]["source_unchanged"])

    def test_source_edit_after_baseline_blocks_build(self):
        self.check()
        (self.job / "plan.md").write_text("Plan.", encoding="utf-8")
        (self.root / "new.txt").write_text("early edit", encoding="utf-8")
        with self.assertRaisesRegex(factory.Refusal, "Source changed after baseline"):
            factory.start_build(self.job, argparse.Namespace(reviewers=["code"]))

    def test_check_configuration_cannot_be_weakened_after_baseline(self):
        self.build()
        config = json.loads((self.job / "checks.json").read_text())
        config[0]["argv"] = [sys.executable, "-c", "pass"]
        (self.job / "checks.json").write_text(json.dumps(config), encoding="utf-8")
        with self.assertRaisesRegex(factory.Refusal, "Checks changed after baseline"):
            self.check()

    def test_plan_and_code_reviewer_are_required(self):
        self.check()
        with self.assertRaisesRegex(factory.Refusal, "nonempty UTF-8"):
            factory.start_build(self.job, argparse.Namespace(reviewers=["code"]))
        (self.job / "plan.md").write_text("Plan.", encoding="utf-8")
        with self.assertRaisesRegex(factory.Refusal, "Select code"):
            factory.start_build(self.job, argparse.Namespace(reviewers=["security"]))

    def test_all_reviews_finish_before_repair(self):
        self.build(("code", "security", "ui"))
        self.check()
        self.assertEqual(self.review("code", "changes")["stage"], "review")
        self.assertEqual(self.review("security")["stage"], "review")
        state = self.review("ui")
        self.assertEqual((state["stage"], state["repairs"]), ("repair", 1))

    def test_material_review_limitation_blocks_completion(self):
        self.build()
        self.check()
        self.assertEqual(self.review(result="incomplete")["stage"], "blocked")
        self.assertFalse(factory.status(self.job)["can_handoff"])

    def test_untracked_file_invalidates_review_evidence(self):
        self.build()
        self.check()
        (self.root / "new.txt").write_text("new source", encoding="utf-8")
        with self.assertRaisesRegex(factory.Refusal, "snapshot is stale"):
            self.review()

    def test_plan_edit_invalidates_review_evidence(self):
        self.build()
        self.check()
        (self.job / "plan.md").write_text("Different scope.", encoding="utf-8")
        with self.assertRaisesRegex(factory.Refusal, "snapshot is stale"):
            self.review()

    def test_wrong_check_run_is_refused(self):
        self.build()
        self.check()
        with self.assertRaisesRegex(factory.Refusal, "different check run"):
            self.review(check_id=1)

    def test_new_check_run_requires_fresh_reviews(self):
        self.build(("code", "security"))
        self.check()
        self.review("code")
        state, code = self.check()
        self.assertEqual((code, state["reviews"]), (0, {}))
        self.assertEqual(self.review("security")["stage"], "review")

    def test_check_evidence_edit_blocks_handoff(self):
        self.build()
        self.check()
        self.review()
        evidence = self.job / "checks" / "run-0002" / "result.json"
        evidence.write_text("{}", encoding="utf-8")
        self.assertFalse(factory.status(self.job)["can_handoff"])

    def test_report_edit_blocks_handoff(self):
        self.build()
        self.check()
        self.review()
        report = self.job / "reviews" / "run-0002" / "code.md"
        report.write_text("Different evidence.", encoding="utf-8")
        self.assertFalse(factory.status(self.job)["can_handoff"])

    def test_code_edit_after_ready_blocks_handoff(self):
        self.build()
        self.check()
        self.review()
        (self.root / "source.txt").write_text("late change\n", encoding="utf-8")
        self.assertFalse(factory.status(self.job)["can_handoff"])

    def test_three_repairs_are_allowed_without_budget_reset_on_resume(self):
        self.build()
        self.check()
        for cycle in range(1, 4):
            state = self.review(result="changes")
            self.assertEqual((state["stage"], state["repairs"]), ("repair", cycle))
            self.state = factory.load(self.job)
            self.check()
        state = self.review(result="changes")
        self.assertEqual((state["stage"], state["repairs"]), ("blocked", 3))
        with self.assertRaisesRegex(factory.Refusal, "stage blocked"):
            self.check()

    def test_failed_checks_consume_the_same_repair_budget(self):
        self.set_checks("fail")
        self.state.update(stage="build", reviewers=["code"],
                          baseline_config=factory.file_digest(self.job / "checks.json"))
        factory.save(self.job, self.state)
        for cycle in range(1, 4):
            state, code = self.check()
            self.assertEqual((code, state["stage"], state["repairs"]), (1, "repair", cycle))
        state, code = self.check()
        self.assertEqual((code, state["stage"], state["repairs"]), (1, "blocked", 3))

    def test_interrupted_baseline_can_be_rerun(self):
        self.state.update(stage="checking", checking_baseline=True, check_count=1)
        factory.save(self.job, self.state)
        state, code = self.check()
        self.assertEqual((code, state["stage"], state["check_count"]), (0, "plan", 2))

    def test_interrupted_build_cannot_reuse_previous_reviews(self):
        self.build()
        self.check()
        with patch.object(factory, "execute_check", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.check()
        state = factory.load(self.job)
        self.assertEqual(state["stage"], "checking")
        self.assertIsNone(state["last_check"])
        state, code = self.check()
        self.assertEqual((code, state["stage"], state["reviews"]), (0, "review", {}))

    def test_interruption_before_attempt_reservation_does_not_block_retry(self):
        with patch.object(factory, "save", side_effect=OSError("interrupted state write")):
            with self.assertRaisesRegex(OSError, "interrupted"):
                self.check()
        self.assertFalse((self.job / "checks" / "run-0001").exists())
        state, code = self.check()
        self.assertEqual((code, state["stage"]), (0, "plan"))

    def test_interruption_after_attempt_reservation_does_not_overwrite_evidence(self):
        original_mkdir = Path.mkdir

        def interrupted_mkdir(path, *args, **kwargs):
            if path.name == "run-0001":
                original_mkdir(path, *args, **kwargs)
                (path / "partial.log").write_text("Preserve evidence.", encoding="utf-8")
                raise OSError("interrupted attempt creation")
            return original_mkdir(path, *args, **kwargs)

        with patch.object(Path, "mkdir", interrupted_mkdir):
            with self.assertRaisesRegex(OSError, "interrupted"):
                self.check()
        state, code = self.check()
        self.assertEqual((code, state["stage"], state["check_count"]), (0, "plan", 2))
        self.assertTrue((self.job / "checks" / "run-0001" / "partial.log").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX process groups are required.")
    def test_timeout_stops_descendants_before_releasing_job(self):
        child = "import time; from pathlib import Path; time.sleep(0.4); Path('late.txt').write_text('late')"
        program = ("import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',"
                   + repr(child) + "]); time.sleep(10)")
        config = [{"name": "child", "argv": [sys.executable, "-c", program], "timeout": 0.1}]
        (self.job / "checks.json").write_text(json.dumps(config), encoding="utf-8")
        state, code = self.check()
        self.assertEqual((code, state["stage"]), (1, "baseline-blocked"))
        time.sleep(0.5)
        self.assertFalse((self.root / "late.txt").exists())

    @unittest.skipUnless(os.name == "posix", "POSIX process groups are required.")
    def test_successful_command_cannot_leave_background_writers(self):
        child = "import time; from pathlib import Path; time.sleep(0.4); Path('late.txt').write_text('late')"
        program = "import subprocess,sys; subprocess.Popen([sys.executable,'-c'," + repr(child) + "])"
        config = [{"name": "child", "argv": [sys.executable, "-c", program]}]
        (self.job / "checks.json").write_text(json.dumps(config), encoding="utf-8")
        state, code = self.check()
        self.assertEqual((code, state["stage"]), (1, "baseline-blocked"))
        self.assertIn("background processes", state["last_check"]["results"][0]["error"])
        time.sleep(0.5)
        self.assertFalse((self.root / "late.txt").exists())

    def test_uncertain_process_cleanup_requires_user_resolution(self):
        with patch.object(factory, "execute_check", side_effect=factory.CleanupFailure("Uncertain cleanup.")):
            state, code = self.check()
        self.assertEqual((code, state["stage"], state["block_kind"]), (1, "blocked", "process"))
        with self.assertRaisesRegex(factory.Refusal, "confirm the blocker"):
            factory.resume(self.job, argparse.Namespace(resolved=False))
        state = factory.resume(self.job, argparse.Namespace(resolved=True))
        self.assertEqual((state["stage"], state["repairs"]), ("baseline", 0))

    def test_resolved_review_blocker_requires_new_checks_and_reviews(self):
        self.build()
        self.check()
        self.review(result="incomplete")
        state = factory.resume(self.job, argparse.Namespace(resolved=True))
        self.assertEqual((state["stage"], state["reviews"]), ("build", {}))
        self.assertIsNone(state["last_check"])
        self.check()
        self.assertEqual(self.review()["stage"], "ready")

    def test_resume_cannot_reset_exhausted_repair_budget(self):
        self.state.update(stage="blocked", block_kind="budget", repairs=3)
        factory.save(self.job, self.state)
        with self.assertRaisesRegex(factory.Refusal, "budgets cannot be reset"):
            factory.resume(self.job, argparse.Namespace(resolved=True))

    def test_unexpected_staging_or_commit_requires_user_intervention(self):
        self.staged = "source.txt\n"
        with self.assertRaisesRegex(factory.Refusal, "Staged changes"):
            self.check()
        self.staged = ""
        self.head = "b" * 40
        with self.assertRaisesRegex(factory.Refusal, "HEAD changed"):
            self.check()

    def test_wrong_branch_is_not_repaired(self):
        self.branch = "another-branch"
        with self.assertRaisesRegex(factory.Refusal, "branch changed"):
            self.check()

    def test_active_lock_prevents_concurrent_state_writes(self):
        (self.job / ".lock").mkdir()
        with self.assertRaisesRegex(factory.Refusal, "locked"):
            self.check()
        self.assertTrue((self.job / ".lock").exists())

    def test_invalid_timeouts_are_refused(self):
        for timeout in (True, 0, -1, float("nan"), float("inf")):
            with self.subTest(timeout=timeout):
                config = [{"name": "bad", "argv": ["test"], "timeout": timeout}]
                (self.job / "checks.json").write_text(json.dumps(config), encoding="utf-8")
                with self.assertRaisesRegex(factory.Refusal, "positive finite"):
                    self.check()

    @unittest.skipUnless(hasattr(os, "symlink"), "Symlinks are unavailable.")
    def test_symlink_target_changes_invalidate_snapshot(self):
        link = self.root / "link"
        try:
            link.symlink_to("source.txt")
        except OSError:
            self.skipTest("Symlink creation is unavailable.")
        before = factory.snapshot(self.job, self.state)
        link.unlink()
        link.symlink_to("elsewhere")
        self.assertNotEqual(before, factory.snapshot(self.job, self.state))


class CreationCase(FactoryFixture):
    def setUp(self):
        super().setUp()
        self.new_root = self.root.parent / "new-worktree"
        self.args = argparse.Namespace(
            confirmed=True, repo=str(self.repo), branch=self.branch, base="main",
            worktree=str(self.new_root), request_file=str(self.job / "request.md"),
        )

    def test_creation_requires_prior_confirmation(self):
        self.args.confirmed = False
        with patch.object(factory.subprocess, "run") as run:
            with self.assertRaisesRegex(factory.Refusal, "Confirm the new branch"):
                factory.create(self.args)
            run.assert_not_called()

    def test_creation_has_one_narrow_git_write_with_hooks_disabled(self):
        def create_worktree(argv, **kwargs):
            self.new_root.mkdir()
            return subprocess.CompletedProcess(argv, 0, "", "")

        with patch.object(factory.subprocess, "run", side_effect=create_worktree) as run:
            state = factory.create(self.args)
        self.assertEqual(state["stage"], "baseline")
        argv = run.call_args.args[0]
        self.assertEqual(argv[0], "git")
        self.assertTrue(argv[2].startswith("core.hooksPath="))
        self.assertEqual(argv[5:], ["worktree", "add", "--no-track", "-b", self.branch,
                                    "--", str(self.new_root), self.head])
        run.assert_called_once()

    def test_existing_directory_is_not_adopted(self):
        self.new_root.mkdir()
        with self.assertRaisesRegex(factory.Refusal, "already exists"):
            factory.create(self.args)

    def test_partial_setup_is_preserved_and_can_resume(self):
        with patch.object(factory.subprocess, "run", side_effect=OSError("blocked by permissions")):
            with self.assertRaisesRegex(OSError, "permissions"):
                factory.create(self.args)
        saved = Path(str(self.new_root) + ".factory")
        self.assertEqual(factory.load(saved)["stage"], "setup")
        self.new_root.mkdir()
        with patch.object(factory.subprocess, "run") as run:
            self.assertEqual(factory.create(self.args)["stage"], "baseline")
            run.assert_not_called()

    def test_unknown_base_never_triggers_fetch(self):
        self.args.base = "unknown"
        with patch.object(factory.subprocess, "run") as run:
            with self.assertRaisesRegex(factory.Refusal, "unavailable locally"):
                factory.create(self.args)
            run.assert_not_called()


class ReadOnlyGitCase(unittest.TestCase):
    def test_git_mutation_is_not_a_read_query(self):
        with patch.object(factory.subprocess, "run") as run:
            for command in ("add", "commit", "fetch", "push", "reset", "config", "worktree"):
                with self.subTest(command=command):
                    with self.assertRaisesRegex(factory.Refusal, "read-only"):
                        factory.read_git(Path.cwd(), command)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
