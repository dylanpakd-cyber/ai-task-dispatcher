"""Tests for the dispatcher itself. stdlib only, no keys, no network.

These pin the behavior documented in docs/: spec parsing, the glob
semantics of allowed/forbidden, the positional porcelain parsing in
changed_paths (do not "fix" it, see docs/troubleshooting.md), and the
worker prompt. Run: python3 -m unittest discover -s tests -v
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dispatch import (SpecError, build_prompt, changed_paths, matches,
                      parse_spec, violations)


def write_spec(tmpdir: str, text: str) -> Path:
    path = Path(tmpdir) / "spec.md"
    path.write_text(text)
    return path


class TestParseSpec(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def parse(self, text: str) -> dict:
        return parse_spec(write_spec(self.tmp.name, text))

    def test_happy_path(self):
        spec = self.parse(
            "goal: implement the thing\n"
            "context: a.py, b.py\n"
            "allowed: src/*, lib/util.py\n"
            "forbidden: tests/*\n"
            "verify: python3 -m unittest\n"
            "done: tests pass\n"
            "budget: 7\n"
            "retries: 3\n"
        )
        self.assertEqual(spec["goal"], "implement the thing")
        self.assertEqual(spec["allowed"], ["src/*", "lib/util.py"])
        self.assertEqual(spec["forbidden"], ["tests/*"])
        self.assertEqual(spec["budget"], 7.0)
        self.assertEqual(spec["retries"], 3)

    def test_goal_required(self):
        with self.assertRaises(SpecError):
            self.parse("verify: true\n")

    def test_verify_required(self):
        with self.assertRaises(SpecError):
            self.parse("goal: do it\n")

    def test_empty_value_is_missing(self):
        with self.assertRaises(SpecError):
            self.parse("goal:\nverify: true\n")

    def test_defaults(self):
        spec = self.parse("goal: g\nverify: true\n")
        self.assertEqual(spec["budget"], 15.0)
        self.assertEqual(spec["retries"], 2)
        self.assertEqual(spec["agent"], "codex")
        self.assertEqual(spec["allowed"], [])
        self.assertEqual(spec["forbidden"], [])

    def test_mock_line_implies_mock_agent(self):
        spec = self.parse("goal: g\nverify: true\nmock: touch done.txt\n")
        self.assertEqual(spec["agent"], "mock")

    def test_explicit_agent_wins_over_mock_inference(self):
        spec = self.parse("goal: g\nverify: true\nagent: claude\nmock: true\n")
        self.assertEqual(spec["agent"], "claude")

    def test_unknown_agent_rejected(self):
        with self.assertRaises(SpecError):
            self.parse("goal: g\nverify: true\nagent: skynet\n")

    def test_non_numeric_budget_is_spec_error(self):
        with self.assertRaises(SpecError):
            self.parse("goal: g\nverify: true\nbudget: [max minutes]\n")

    def test_non_numeric_retries_is_spec_error(self):
        with self.assertRaises(SpecError):
            self.parse("goal: g\nverify: true\nretries: lots\n")

    def test_retries_floor_is_one(self):
        spec = self.parse("goal: g\nverify: true\nretries: 0\n")
        self.assertEqual(spec["retries"], 1)

    def test_keys_case_insensitive(self):
        spec = self.parse("GOAL: g\nVerify: true\n")
        self.assertEqual(spec["goal"], "g")
        self.assertEqual(spec["verify"], "true")

    def test_indented_continuation_lines_append(self):
        spec = self.parse("goal: first line\n  second line\nverify: true\n")
        self.assertEqual(spec["goal"], "first line\nsecond line")

    def test_newline_separated_lists(self):
        spec = self.parse(
            "goal: g\nverify: true\nallowed: a.py\n  b.py\n  c/\n"
        )
        self.assertEqual(spec["allowed"], ["a.py", "b.py", "c/"])

    def test_prose_between_keys_ignored(self):
        spec = self.parse(
            "# a heading\n\nSome prose about the task.\n\n"
            "goal: g\n\nMore prose.\n\nverify: true\n"
        )
        self.assertEqual(spec["goal"], "g")
        self.assertEqual(spec["verify"], "true")


class TestMatching(unittest.TestCase):
    def test_glob(self):
        self.assertTrue(matches("tests/test_calc.py", "tests/*"))
        self.assertFalse(matches("calc.py", "tests/*"))

    def test_directory_prefix(self):
        self.assertTrue(matches("src/deep/nested/file.py", "src"))
        self.assertFalse(matches("srcfile.py", "src"))

    def test_trailing_slash_stripped(self):
        self.assertTrue(matches("tests/test_calc.py", "tests/"))

    def test_exact_file(self):
        self.assertTrue(matches("calc.py", "calc.py"))
        self.assertFalse(matches("calc.pyc", "calc.py"))

    def test_forbidden_reported_first(self):
        bad = violations(["tests/test_calc.py"], ["calc.py"], ["tests/*"])
        self.assertEqual(bad, ["forbidden path touched: tests/test_calc.py"])

    def test_outside_allowed_reported(self):
        bad = violations(["other.py"], ["calc.py"], ["tests/*"])
        self.assertEqual(bad, ["path outside allowed list: other.py"])

    def test_empty_allowed_list_allows_anything_not_forbidden(self):
        self.assertEqual(violations(["anything.py"], [], ["tests/*"]), [])

    def test_clean_run_has_no_violations(self):
        self.assertEqual(violations(["calc.py"], ["calc.py"], ["tests/*"]), [])


class TestChangedPaths(unittest.TestCase):
    """changed_paths parses `git status --porcelain` positionally.

    Porcelain v1 lines are `XY path`; a modified-unstaged line starts
    with a space, so the parser must NOT strip lines. These tests pin
    that against a real git repo.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@ngnm")
        self.git("config", "user.name", "ngnm test")
        (self.repo / "tracked.py").write_text("x = 1\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "seed")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True,
                       capture_output=True, text=True)

    def test_modified_unstaged_file(self):
        (self.repo / "tracked.py").write_text("x = 2\n")
        self.assertEqual(changed_paths(self.repo), ["tracked.py"])

    def test_untracked_file(self):
        (self.repo / "new.py").write_text("y = 1\n")
        self.assertEqual(changed_paths(self.repo), ["new.py"])

    def test_rename_reports_new_path(self):
        self.git("mv", "tracked.py", "renamed.py")
        self.assertEqual(changed_paths(self.repo), ["renamed.py"])

    def test_pycache_and_pyc_filtered(self):
        cache = self.repo / "__pycache__"
        cache.mkdir()
        (cache / "tracked.cpython-312.pyc").write_text("")
        (self.repo / "stray.pyc").write_text("")
        self.assertEqual(changed_paths(self.repo), [])

    def test_ngnm_dir_filtered(self):
        internal = self.repo / ".ngnm" / "logs"
        internal.mkdir(parents=True)
        (internal / "run.log").write_text("")
        self.assertEqual(changed_paths(self.repo), [])

    def test_clean_tree_is_empty(self):
        self.assertEqual(changed_paths(self.repo), [])


class TestBuildPrompt(unittest.TestCase):
    def spec(self):
        return {"raw": "goal: g\nverify: true\n", "retries": 2}

    def test_contains_raw_spec_and_rules(self):
        prompt = build_prompt(self.spec(), 1, "")
        self.assertIn("goal: g", prompt)
        self.assertIn("Attempt 1 of 2", prompt)
        self.assertIn("Never touch forbidden paths", prompt)
        self.assertNotIn("PREVIOUS ATTEMPT FAILED", prompt)

    def test_feedback_appears_on_retry(self):
        prompt = build_prompt(self.spec(), 2, "verify exited 1\nboom")
        self.assertIn("PREVIOUS ATTEMPT FAILED", prompt)
        self.assertIn("boom", prompt)


if __name__ == "__main__":
    unittest.main()
