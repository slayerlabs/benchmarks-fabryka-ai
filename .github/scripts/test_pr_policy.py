"""Tests for the PR policy check. Run: python3 -m unittest discover -s .github/scripts -p "test_pr_policy.py" """

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pr_policy as P  # noqa: E402

TEMPLATE = (Path(__file__).resolve().parents[1] / "pull_request_template.md").read_text(encoding="utf-8")

FILLED = """\
## Problem or current behavior
CodeSOTA CI did not run on pull requests that changed only the workflow file itself.

## Result or new behavior
The workflow now lists its own path among the changes that trigger the test job.

## Scope
- [ ] `benchmarks/` (`codesota` package)
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
                  "docs(contributing/benchmarks): fix link"):
            self.assertEqual(P.check_title(t), [], t)

    def test_other_titles_fail(self) -> None:
        for t in ("Fix the thing", "fix:missing space", "feature: x", "Fix: capitalised type",
                  "przebieg: licz bez listy", "fix(Benchmarks): upper-case scope", "fix: "):
            self.assertNotEqual(P.check_title(t), [], t)

    def test_long_title_fails(self) -> None:
        self.assertTrue(any("characters" in e for e in P.check_title("fix: " + "x" * 120)))


class Body(unittest.TestCase):
    def test_filled_description_passes(self) -> None:
        self.assertEqual(P.check("ci: run CodeSOTA CI on workflow changes", FILLED, 500).errors, ())

    def test_unfilled_template_fails_every_required_section(self) -> None:
        errors = P.check("fix: something", TEMPLATE, 500).errors
        for name in P.SECTIONS:
            self.assertTrue(any(f"'{name}'" in e or f"## {name}" in e for e in errors), name)

    def test_comments_do_not_count_as_content(self) -> None:
        body = fill(**{"CodeSOTA CI did not run on pull requests that changed only the workflow file itself.":
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

    def test_long_heading_lines_are_fast(self) -> None:
        # Review 2: the old heading regex backtracked cubically ("## a" + spaces + "b" took 8.6 s at 2000 spaces).
        body = FILLED + "\n## a" + " " * 60000 + "b\n" + ("## x  " + " " * 3000 + "#\n") * 20
        start = time.perf_counter()
        P.check_body(body, False)
        self.assertLess(time.perf_counter() - start, 1.0)

    def test_unclosed_fence_hides_the_rest_like_github(self) -> None:
        body = FILLED.replace("## Validation", "```\n## Validation")
        self.assertTrue(any("Validation" in e for e in P.check_body(body, False)))

    def test_fence_opener_inside_a_comment_is_ignored(self) -> None:
        body = FILLED.replace("No migration required.", "No migration required.\n<!-- ``` -->")
        self.assertEqual(P.check_body(body, False), [])

    def test_indented_and_closed_headings_count(self) -> None:
        body = FILLED.replace("## Validation", "   ## Validation ##").replace("## Scope", "### Scope ###")
        self.assertEqual(P.check_body(body, False), [])

    def test_four_spaces_is_not_a_heading(self) -> None:
        body = FILLED.replace("## Validation", "    ## Validation")
        self.assertIn("Missing section '## Validation' (from .github/pull_request_template.md).",
                      P.check_body(body, False))

    def test_issue_zero_is_not_a_reference(self) -> None:
        self.assertTrue(any("Related issue" in e for e in P.check_body(FILLED.replace("Refs #42", "Refs #0"), False)))

    def test_empty_code_block_is_not_content(self) -> None:
        # Review 3: an empty fenced block used to count as 20 characters of content.
        body = FILLED.replace("Ran `python3 -m unittest discover -s .github/scripts`: 30 tests, OK.", "```\n\n```")
        self.assertTrue(any("Validation" in e for e in P.check_body(body, False)))

    def test_code_block_with_real_output_is_content(self) -> None:
        body = FILLED.replace("Ran `python3 -m unittest discover -s .github/scripts`: 30 tests, OK.",
                              "```\n$ python3 -m unittest discover -s .github/scripts\nRan 30 tests\nOK\n```")
        self.assertEqual(P.check_body(body, False), [])

    def test_unclosed_comment_mid_line_is_text(self) -> None:
        # Review 3: "text <!-- note" mid-line hid every later section; GitHub shows it literally.
        body = FILLED.replace("No migration required.", "No migration required. <!-- see the docs")
        self.assertEqual(P.check_body(body, False), [])

    def test_unclosed_comment_at_line_start_hides_the_rest(self) -> None:
        body = FILLED.replace("## Validation", "<!-- draft\n## Validation")
        self.assertTrue(any("Validation" in e for e in P.check_body(body, False)))

    def test_mixed_fence_line_does_not_close_a_block(self) -> None:
        body = FILLED.replace("No migration required.", "No migration required.\n```\n```~~~\n## Validation\nx\n```")
        self.assertEqual(P.check_body(body, False), [])  # the real Validation section below still counts

    def test_backtick_in_info_string_is_not_a_fence(self) -> None:
        body = FILLED.replace("No migration required.", "No migration required. ```py`x")
        body = body.replace("No migration required. ```py`x", "No migration required.\n```py`x")
        self.assertEqual(P.check_body(body, False), [])

    def test_a_later_no_issue_reason_counts(self) -> None:
        body = FILLED.replace("Refs #42", "No issue: see above\nNo issue: a one-line typo fix in a comment")
        self.assertEqual(P.check_body(body, False), [])

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

    def test_docs_title_without_the_docs_box_needs_every_section(self) -> None:
        # Review 2: a code PR titled "docs: ..." could skip Validation and AI assistance.
        body = self.SHORT.replace("- [x] Documentation only", "- [x] `benchmarks/` (`codesota` package)")
        errors = P.check("docs: fix setup command", body, 500).errors
        self.assertTrue(any("Validation" in e for e in errors))
        self.assertTrue(any("AI assistance" in e for e in errors))


class Research(unittest.TestCase):
    """PRs that change only research/: a benchmark one person runs from start to end (CONTRIBUTING.md)."""

    TITLE = "IFEval: Slayer 1B 1.08 and Bielik 11B v3.1"
    BODY = """\
## What this PR changes

Adds IFEval (541 prompts, `prompt_level_strict_acc`) in `research/api-benchmarks/ifeval/`.

Refs #298

## Checklist

- [x] Pre-PR commands from CONTRIBUTING.md exit 0
"""
    LISTING = "research/api-benchmarks/ifeval/README.md\t\nresearch/api-benchmarks/ifeval/run.sh\t\n"

    def test_benchmark_pr_passes_in_its_own_layout(self) -> None:
        self.assertEqual(P.check(self.TITLE, self.BODY, 500, research=True).errors, ())

    def test_same_pr_outside_research_needs_the_full_form(self) -> None:
        errors = P.check(self.TITLE, self.BODY, 500).errors
        self.assertTrue(any("Conventional Commits" in e for e in errors))
        self.assertTrue(any("Validation" in e for e in errors))

    def test_issue_reference_is_required(self) -> None:
        errors = P.check(self.TITLE, self.BODY.replace("Refs #298", ""), 500, research=True).errors
        self.assertTrue(any("Refs #<number>" in e for e in errors))
        self.assertEqual(P.check(self.TITLE, self.BODY.replace("Refs #298", "No issue: a rerun on new hardware"),
                                 500, research=True).errors, ())

    def test_description_must_say_more_than_the_issue(self) -> None:
        self.assertTrue(P.check(self.TITLE, "Refs #298", 500, research=True).errors)
        self.assertTrue(P.check(self.TITLE, "<!-- Adds IFEval results for two models. -->\nRefs #298", 500,
                                research=True).errors)

    def test_title_must_exist_and_stay_short(self) -> None:
        self.assertTrue(P.check("  ", self.BODY, 500, research=True).errors)
        self.assertTrue(P.check("x" * (P.TITLE_MAX + 1), self.BODY, 500, research=True).errors)

    def test_only_research_files_select_the_research_form(self) -> None:
        self.assertTrue(P.research_only(self.LISTING, 2))
        self.assertFalse(P.research_only(self.LISTING + "benchmarks/src/x.py\t\n", 3))
        self.assertFalse(P.research_only(self.LISTING + ".github/workflows/research-tests.yml\t\n", 3))

    def test_rename_out_of_another_area_needs_the_full_form(self) -> None:
        self.assertFalse(P.research_only("research/x.py\tbenchmarks/x.py\n", 1))

    def test_incomplete_or_missing_listing_needs_the_full_form(self) -> None:
        self.assertFalse(P.research_only(self.LISTING, 3))
        self.assertFalse(P.research_only("", 0))
        self.assertFalse(P.research_only(self.LISTING, P.MAX_LISTED))


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

    def run_script(self, title: str, body: str, number: str, **extra: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PR_TITLE": title, "PR_BODY": body, "PR_NUMBER": number, **extra}
        return subprocess.run([sys.executable, str(Path(P.__file__))], env=env, capture_output=True, text=True)

    def run_with_listing(self, listing: str, count: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "files.tsv"
            path.write_text(listing, encoding="utf-8")
            return self.run_script(Research.TITLE, Research.BODY, "500", PR_FILES=str(path), CHANGED_FILES=count)

    def test_research_listing_selects_the_research_form(self) -> None:
        r = self.run_with_listing(Research.LISTING, "2")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("research form", r.stdout)

    def test_listing_with_other_files_keeps_the_full_form(self) -> None:
        r = self.run_with_listing(Research.LISTING + "benchmarks/x.py\t\n", "3")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Conventional Commits", r.stdout)

    def test_listing_without_a_file_count_is_rejected(self) -> None:
        self.assertNotEqual(self.run_with_listing(Research.LISTING, "").returncode, 0)

    def test_pass_exits_zero(self) -> None:
        r = self.run_script("ci: run CodeSOTA CI on workflow changes", FILLED, "500")
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
    """pr-policy.yml must decide with the default branch's checker, never the PR's copy, and run no PR code."""

    text = (WORKFLOWS / "pr-policy.yml").read_text(encoding="utf-8")
    code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())

    def test_runs_on_pull_request_only(self) -> None:
        self.assertRegex(self.code, r"(?m)^  pull_request:")
        self.assertNotIn("pull_request_target", self.code)

    def test_checks_out_only_the_default_branch_checker(self) -> None:
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.code)
        self.assertIn("path: trusted", self.code)
        self.assertIn("sparse-checkout: .github/scripts/pr_policy.py", self.code)
        self.assertIn("persist-credentials: false", self.code)
        self.assertEqual(self.code.count("actions/checkout@"), 1)

    def test_bootstrap_pass_is_limited_to_the_bootstrap_pr(self) -> None:
        # Review 3: without a limit, deleting the checker on main would make every later PR pass.
        self.assertIn(f'[ "$PR_NUMBER" -le {P.FIRST_ENFORCED_PR} ]', self.code)
        self.assertIn("::error::The default branch has no .github/scripts/pr_policy.py", self.code)

    def test_runs_the_trusted_copy_not_the_pr_copy(self) -> None:
        self.assertIn("python3 trusted/.github/scripts/pr_policy.py", self.code)
        self.assertNotRegex(self.code, r"python3 \.github/scripts/pr_policy\.py")

    def test_no_head_code_secrets_or_write_permissions(self) -> None:
        for forbidden in ("head.sha", "head.ref", "head.repo", "refs/pull", "secrets.", ": write",
                          "actions/cache", "download-artifact"):
            self.assertNotIn(forbidden, self.code, forbidden)

    def test_research_form_is_chosen_from_githubs_file_list(self) -> None:
        self.assertIn('gh api --paginate "repos/$REPO/pulls/$PR/files"', self.code)
        self.assertIn("CHANGED_FILES: ${{ github.event.pull_request.changed_files }}", self.code)
        self.assertIn("PR_FILES: ${{ runner.temp }}/files.tsv", self.code)

    def run_blocks(self) -> list[str]:
        """The shell script of every `run: |` step: the lines indented deeper than the `run:` key."""
        blocks, lines = [], self.code.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "run: |":
                key = len(line) - len(line.lstrip())
                script = []
                for nxt in lines[i + 1:]:
                    if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= key:
                        break
                    script.append(nxt)
                blocks.append("\n".join(script))
        return blocks

    def test_untrusted_text_only_through_env(self) -> None:
        blocks = self.run_blocks()
        self.assertEqual(len(blocks), 2)
        for run in blocks:
            self.assertNotIn("${{", run)
        self.assertIn("PR_TITLE: ${{ github.event.pull_request.title }}", self.code)
        self.assertIn("PR_BODY: ${{ github.event.pull_request.body }}", self.code)

    def test_no_workflow_uses_pull_request_target(self) -> None:
        users = []
        for p in sorted(WORKFLOWS.glob("*.yml")):
            body = "\n".join(line.split("#", 1)[0] for line in p.read_text(encoding="utf-8").splitlines())
            if "pull_request_target" in body:
                users.append(p.name)
        self.assertEqual(users, [])


if __name__ == "__main__":
    unittest.main()
