"""Tests for the v2 change detection. Run: python3 -m unittest discover -s .github/scripts -p "test_codesota_changes.py" """

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import codesota_changes as C  # noqa: E402

WORKFLOW = (Path(__file__).resolve().parents[1] / "workflows" / "codesota.yml").read_text(encoding="utf-8")


def listing(*paths: str) -> list[str]:
    return [p if "\t" in p else p + "\t" for p in paths]


class Decision(unittest.TestCase):
    def test_docs_and_research_only_skip_tests(self) -> None:
        self.assertFalse(C.needs_tests(listing("README.md", "research/tools/x.sh", "docs/a.md"), 3))

    def test_benchmarks_change_runs_tests(self) -> None:
        self.assertTrue(C.needs_tests(listing("README.md", "benchmarks/README.md"), 2))

    def test_workflow_and_detector_changes_run_tests(self) -> None:
        self.assertTrue(C.needs_tests(listing(".github/workflows/codesota.yml"), 1))
        self.assertTrue(C.needs_tests(listing(".github/scripts/codesota_changes.py"), 1))

    def test_rename_out_of_benchmarks_runs_tests(self) -> None:
        self.assertTrue(C.needs_tests(["research/x.py\tbenchmarks/src/codesota/x.py"], 1))

    def test_lookalike_paths_do_not_count(self) -> None:
        self.assertFalse(C.needs_tests(listing("xbenchmarks/a", ".github/workflows/codesota.yml.bak"), 2))

    def test_truncated_listing_fails_closed(self) -> None:
        # 3000-file API cap, or fewer files listed than the PR has: run the tests.
        self.assertTrue(C.needs_tests(listing("README.md"), C.MAX_LISTED))
        self.assertTrue(C.needs_tests(listing("README.md"), 2))

    def test_large_listing_with_an_early_match(self) -> None:
        # The SIGPIPE case from the first review: a match early in a long listing must still count.
        lines = listing("benchmarks/a.py", *[f"research/r/{i}.json" for i in range(2500)])
        self.assertTrue(C.needs_tests(lines, len(lines)))


class CommandLine(unittest.TestCase):
    def run_script(self, stdin: str, changed: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "CHANGED_FILES": changed}
        return subprocess.run([sys.executable, C.__file__], input=stdin, env=env, capture_output=True, text=True)

    def test_prints_github_output_line(self) -> None:
        self.assertEqual(self.run_script("benchmarks/x\t\n", "1").stdout.strip(), "v2=true")
        self.assertEqual(self.run_script("README.md\t\n", "1").stdout.strip(), "v2=false")

    def test_bad_count_is_an_error_not_a_skip(self) -> None:
        r = self.run_script("README.md\t\n", "")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")


class WorkflowWiring(unittest.TestCase):
    """Literal wiring guards on codesota.yml (string checks, not behavior): the workflow feeds the script what it
    expects and calls the tested verdict. The behavior is tested in Decision and Verdict, and was checked on GitHub."""

    def test_listing_includes_previous_filenames(self) -> None:
        self.assertIn('[.filename, (.previous_filename // "")] | @tsv', WORKFLOW)

    def test_changed_files_count_comes_from_the_event(self) -> None:
        self.assertIn("CHANGED_FILES: ${{ github.event.pull_request.changed_files }}", WORKFLOW)

    def test_aggregator_uses_the_tested_verdict(self) -> None:
        self.assertIn("python3 .github/scripts/codesota_changes.py --verdict", WORKFLOW)
        self.assertIn("if: always()", WORKFLOW)


class Verdict(unittest.TestCase):
    def test_truth_table(self) -> None:
        cases = {
            ("success", "true", "success"): True,
            ("success", "false", "skipped"): True,
            ("success", "true", "skipped"): False,  # tests needed but did not run
            ("success", "false", "success"): False,  # inconsistent: detection said no, tests ran anyway
            ("success", "true", "failure"): False,  # includes timeouts
            ("success", "true", "cancelled"): False,
            ("success", "", "skipped"): False,  # no definite decision
            ("failure", "", "skipped"): False,  # detection failed (API error, rate limit)
            ("cancelled", "", "skipped"): False,
        }
        for args, expected in cases.items():
            self.assertIs(C.verdict(*args), expected, args)

    def test_command_line_exit_codes(self) -> None:
        for env, code in ((("success", "false", "skipped")), 0), ((("success", "true", "skipped")), 1):
            e = {**os.environ, "CHANGES": env[0], "V2": env[1], "TEST": env[2]}
            r = subprocess.run([sys.executable, C.__file__, "--verdict"], env=e, capture_output=True, text=True)
            self.assertEqual(r.returncode, code, r.stdout)

    def test_every_job_has_a_timeout(self) -> None:
        self.assertEqual(WORKFLOW.count("timeout-minutes:"), WORKFLOW.count("runs-on:"))


if __name__ == "__main__":
    unittest.main()
