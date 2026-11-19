"""Tests for the PR policy check. Run: python3 -m unittest discover -s .github/scripts -p "test_pr_policy.py" """

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pr_policy as P  # noqa: E402

TEMPLATE = (Path(__file__).resolve().parents[1] / "pull_request_template.md").read_text(encoding="utf-8")

FILLED = """\
## Problem or current behavior
The v2 CI did not run on pull requests that changed only the workflow file itself.

## Result or new behavior
The workflow now lists its own path among the changes that trigger the test job.

## Scope
- [ ] `benchmarks/` (CodeSOTA v2)
- [x] Repository infrastructure (`.github/`, CI, policy)

## Compatibility and migration
No migration required.

## Evaluation methodology impact
None

## Validation
Ran `python3 -m unittest discover -s .github/scripts`: 30 tests, OK.

## Related issue
Refs #42

## AI assistance
None
"""


def fill(**replace: str) -> str:
    body = FILLED
    for old, new in replace.items():
        body = body.replace(old.replace("_", " "), new)
    return body


class Title(unittest.TestCase):
    def test_conventional_titles_pass(self) -> None:
        for t in ("fix: handle empty body", "feat(benchmarks): add task", "ci!: drop python 3.10",
                  "docs(contributing/v2): fix link"):
            self.assertEqual(P.check_title(t), [], t)

    def test_other_titles_fail(self) -> None:
        for t in ("Fix the thing", "fix:missing space", "feature: x", "Fix: capitalised type",
                  "przebieg: licz bez listy", "fix(Benchmarks): upper-case scope", "fix: "):
            self.assertNotEqual(P.check_title(t), [], t)

    def test_long_title_fails(self) -> None:
        self.assertTrue(any("characters" in e for e in P.check_title("fix: " + "x" * 120)))


class Body(unittest.TestCase):
    def test_filled_description_passes(self) -> None:
        self.assertEqual(P.check("ci: run v2 CI on workflow changes", FILLED, 500).errors, ())

    def test_unfilled_template_fails_every_required_section(self) -> None:
        errors = P.check("fix: something", TEMPLATE, 500).errors
        for name in P.SECTIONS:
            self.assertTrue(any(f"'{name}'" in e or f"## {name}" in e for e in errors), name)

    def test_comments_do_not_count_as_content(self) -> None:
        body = fill(**{"The v2 CI did not run on pull requests that changed only the workflow file itself.":
                       "<!-- explain the problem here, with enough words to pass a length check -->"})
        self.assertIn("Section 'Problem or current behavior' is empty or a placeholder.", P.check_body(body, False))

    def test_unterminated_comment_hides_the_rest(self) -> None:
        body = FILLED.replace("## Validation", "<!-- unterminated\n## Validation")
        self.assertTrue(any("Validation" in e for e in P.check_body(body, False)))

    def test_placeholders_fail(self) -> None:
        for word in ("N/A", "TODO", "tbd.", "-", "..."):
            body = FILLED.replace("The workflow now lists its own path among the changes that trigger the test job.",
                                  word)
            self.assertTrue(any("Result or new behavior" in e for e in P.check_body(body, False)), word)

    def test_too_short_narrative_fails(self) -> None:
        body = FILLED.replace("Ran `python3 -m unittest discover -s .github/scripts`: 30 tests, OK.", "tested")
        self.assertIn("too short", " ".join(P.check_body(body, False)))

    def test_none_is_fine_where_none_is_an_answer(self) -> None:
        self.assertEqual(P.check_body(FILLED, False), [])  # methodology impact and AI assistance say "None"

    def test_missing_section_fails(self) -> None:
        body = FILLED.replace("## Compatibility and migration\nNo migration required.\n", "")
        self.assertIn("Missing section '## Compatibility and migration' (from .github/pull_request_template.md).",
                      P.check_body(body, False))

    def test_scope_needs_a_ticked_box(self) -> None:
        body = FILLED.replace("- [x] Repository", "- [ ] Repository")
        self.assertIn("Section 'Scope': tick at least one box.", P.check_body(body, False))

    def test_issue_reference_forms(self) -> None:
        for ref in ("Refs #42", "Closes #7", "fixes: #9", "No issue: one-line typo fix in a comment"):
            self.assertEqual(P.check_body(FILLED.replace("Refs #42", ref), False), [], ref)
        for ref in ("#42", "No issue: <reason>", "No issue:", "see board"):
            self.assertTrue(any("Related issue" in e for e in P.check_body(FILLED.replace("Refs #42", ref), False)),
                            ref)

    def test_windows_line_endings_and_level_three_headings(self) -> None:
        body = FILLED.replace("## ", "### ").replace("\n", "\r\n")
        self.assertEqual(P.check_body(body, False), [])

    def test_comment_marker_in_inline_code_is_text(self) -> None:
        body = FILLED.replace("Ran `python3", "Searched with `grep '<!--' x` and ran `python3")
        self.assertEqual(P.check_body(body, False), [])

    def test_heading_in_fenced_code_is_text(self) -> None:
        body = FILLED.replace("No migration required.", "No migration required.\n\n```md\n## Validation\nTODO\n```")
        self.assertEqual(P.check_body(body, False), [])

    def test_no_issue_with_placeholder_reason_fails(self) -> None:
        for reason in ("No issue: TODO.", "No issue: n/a", "No issue: tbd"):
            self.assertTrue(any("Related issue" in e for e in P.check_body(FILLED.replace("Refs #42", reason), False)),
                            reason)

    def test_empty_body_fails(self) -> None:
        self.assertEqual(len(P.check_body("", False)), len(P.SECTIONS))


class DocsOnly(unittest.TestCase):
    SHORT = """\
## Problem or current behavior
The setup command in benchmarks/README.md had a typo in the directory name.

## Result or new behavior
The command now names the right directory and runs as written.

## Scope
- [x] Documentation only

## Related issue
No issue: a one-word typo fix
"""

    def test_docs_title_needs_only_four_sections(self) -> None:
        self.assertEqual(P.check("docs: fix setup command", self.SHORT, 500).errors, ())

    def test_same_body_with_a_code_title_fails(self) -> None:
        self.assertNotEqual(P.check("fix: setup command", self.SHORT, 500).errors, ())


class Grandfathering(unittest.TestCase):
    def test_old_pr_reports_but_passes(self) -> None:
        r = P.check("przebieg: stara konwencja", "", P.FIRST_ENFORCED_PR - 1)
        self.assertTrue(r.errors)
        self.assertFalse(r.enforced)
        self.assertTrue(r.passed)

    def test_new_pr_is_enforced(self) -> None:
        r = P.check("przebieg: stara konwencja", "", P.FIRST_ENFORCED_PR)
        self.assertTrue(r.enforced)
        self.assertFalse(r.passed)


class CommandLine(unittest.TestCase):
    """The script reads only environment variables; shell metacharacters in them stay data."""

    def run_script(self, title: str, body: str, number: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PR_TITLE": title, "PR_BODY": body, "PR_NUMBER": number}
        return subprocess.run([sys.executable, str(Path(P.__file__))], env=env, capture_output=True, text=True)

    def test_pass_exits_zero(self) -> None:
        r = self.run_script("ci: run v2 CI on workflow changes", FILLED, "500")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_fail_exits_one_with_error_annotations(self) -> None:
        r = self.run_script("$(touch /tmp/pwned) `id`", "", "500")
        self.assertEqual(r.returncode, 1)
        self.assertIn("::error::", r.stdout)

    def test_annotation_escapes_newlines_and_percent(self) -> None:
        line = P.annotation("error", "bad\r\n::set-output name=x::y 100%")
        self.assertEqual(line, "::error::bad%0D%0A::set-output name=x::y 100%25")
        self.assertNotIn("\n", line)

    def test_old_pr_exits_zero_with_notices(self) -> None:
        r = self.run_script("Stary tytul", "", str(P.FIRST_ENFORCED_PR - 1))
        self.assertEqual(r.returncode, 0)
        self.assertIn("::notice::", r.stdout)

    def test_bad_number_is_rejected(self) -> None:
        self.assertNotEqual(self.run_script("fix: x", FILLED, "12; rm -rf /").returncode, 0)


WORKFLOWS = Path(__file__).resolve().parents[1] / "workflows"


class PolicyWorkflowTrust(unittest.TestCase):
    """pr-policy.yml must run the base branch's checker, never PR code (the PR controls `pull_request` workflows)."""

    text = (WORKFLOWS / "pr-policy.yml").read_text(encoding="utf-8")

    def test_runs_on_pull_request_target_only(self) -> None:
        self.assertRegex(self.text, r"(?m)^  pull_request_target:")
        self.assertNotRegex(self.text, r"(?m)^  pull_request:")

    def test_checks_out_only_the_base_branch_checker(self) -> None:
        self.assertIn("ref: ${{ github.event.pull_request.base.ref }}", self.text)
        self.assertIn("sparse-checkout: .github/scripts/pr_policy.py", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_no_head_code_secrets_or_write_permissions(self) -> None:
        code = "\n".join(line.split("#", 1)[0] for line in self.text.splitlines())
        for forbidden in ("head.sha", "head.ref", "head.repo", "refs/pull", "secrets.", ": write",
                          "actions/cache", "download-artifact"):
            self.assertNotIn(forbidden, code, forbidden)

    def test_untrusted_text_only_through_env(self) -> None:
        run_lines = [line for line in self.text.splitlines() if line.strip().startswith("run:")]
        self.assertEqual(run_lines, ["        run: python3 .github/scripts/pr_policy.py"])

    def test_no_other_workflow_uses_pull_request_target(self) -> None:
        users = sorted(p.name for p in WORKFLOWS.glob("*.yml")
                       if "pull_request_target" in p.read_text(encoding="utf-8").split("\non:", 1)[-1][:400])
        self.assertEqual(users, ["pr-policy.yml"])


if __name__ == "__main__":
    unittest.main()
