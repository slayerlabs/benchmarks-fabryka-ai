"""Structural check of a pull request's title and description against .github/pull_request_template.md.

It checks structure only: a Conventional Commits title, the required sections, real content in them (an HTML comment
or a placeholder does not count), at least one ticked scope box, and an issue reference or a stated reason for none.
It does not judge whether the change is good; reviewers do.

A PR that changes only files under research/ (a benchmark one person runs from start to end, CONTRIBUTING.md) is
checked in a lighter form: a title of at most TITLE_MAX characters in any style, a description in any layout, and an
issue reference. Which form applies is decided from GitHub's list of the PR's files, never from the PR's text, and
falls back to the full form when that list is missing or may be incomplete.

Input comes from environment variables, never from the command line, so untrusted text never passes through a shell:
PR_TITLE, PR_BODY, PR_NUMBER, and optionally PR_FILES (path of a file with one changed file per line as
`<filename>\t<previous_filename or empty>`, from `gh api --paginate repos/{repo}/pulls/{n}/files --jq '.[] |
[.filename, (.previous_filename // "")] | @tsv'`) with CHANGED_FILES (the PR's `changed_files` count). Exit code 0
when the PR passes (or predates the policy), 1 otherwise.

    PR_TITLE="docs: fix link" PR_BODY="$(cat body.md)" PR_NUMBER=400 python3 .github/scripts/pr_policy.py
"""

import os
import re
import sys
from dataclasses import dataclass

FIRST_ENFORCED_PR = 310
"""PRs numbered below this were opened before the policy and its template existed: they get the report as a notice,
and the check passes. This is the number of the PR that introduced the policy."""

TYPES = ("build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "revert", "style", "test")
TITLE = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([a-z0-9][a-z0-9._/-]*\))?!?: \S.*$")
TITLE_MAX = 100

SECTIONS = (
    "Problem or current behavior",
    "Result or new behavior",
    "Scope",
    "Compatibility and migration",
    "Evaluation methodology impact",
    "Validation",
    "Related issue",
    "AI assistance",
)
DOCS_SECTIONS = ("Problem or current behavior", "Result or new behavior", "Scope", "Related issue")
"""Trivial documentation PRs (title type "docs") need only these."""

NARRATIVE = ("Problem or current behavior", "Result or new behavior", "Validation")
"""Sections that must say something specific: at least NARRATIVE_MIN characters and not a placeholder word."""
NARRATIVE_MIN = 20
PLACEHOLDERS = {"", "-", "n/a", "na", "tbd", "todo", "...", "wip", "same", "see above", "see title"}

ISSUE = re.compile(r"\b(?:Refs|Closes|Fixes|Resolves):? #[1-9]\d*\b", re.IGNORECASE)
NO_ISSUE = re.compile(r"^No issue: *(?!<)\S.{4,}", re.IGNORECASE | re.MULTILINE)
CHECKED = re.compile(r"^\s*[-*] \[[xX]\] ", re.MULTILINE)
DOCS_BOX = re.compile(r"^\s*[-*] \[[xX]\] Documentation only\b", re.MULTILINE)

RESEARCH_PREFIX = "research/"
MAX_LISTED = 3000
"""GitHub's "list pull request files" endpoint returns at most 3000 files."""


@dataclass(frozen=True)
class Result:
    errors: tuple[str, ...]
    enforced: bool

    @property
    def passed(self) -> bool:
        return not self.errors or not self.enforced


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def fence_opener(line: str) -> str | None:
    """The fence (``` or ~~~, possibly longer) if the line opens a fenced code block, as in GitHub Flavored Markdown:
    at most 3 spaces of indent, and a backtick fence's info string contains no backtick."""
    if indent(line) > 3:
        return None
    rest = line.lstrip(" ")
    for ch in ("`", "~"):
        n = len(rest) - len(rest.lstrip(ch))
        if n >= 3 and not (ch == "`" and "`" in rest[n:]):
            return ch * n
    return None


def closes_fence(line: str, fence: str) -> bool:
    """A closing fence: at most 3 spaces of indent, the same character at least as long as the opener, then spaces."""
    rest = line.strip(" ")
    return indent(line) <= 3 and len(rest) >= len(fence) and set(rest) == {fence[0]}


def visible_lines(body: str) -> list[str]:
    """The body's lines as GitHub would show them for structure, in one linear pass (no input can make it slow):

    - HTML comments are removed. A comment that is not closed on its line hides the following lines only when it starts
      the line, as an HTML block does; mid-line, an unclosed "<!--" is plain text.
    - Code is kept as content but can never be structure: fenced block lines are indented by 4 spaces (so none is a
      heading) and the fence lines themselves dropped; an unclosed fence runs to the end, as in GitHub. Inline code
      keeps its text, and nothing inside it starts a comment.
    """
    out: list[str] = []
    fence: str | None = None
    in_comment = False
    for line in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if fence is not None:
            if closes_fence(line, fence):
                fence = None
            else:
                out.append("    " + line if line.strip() else "")
            continue
        if not in_comment and (opener := fence_opener(line)) is not None:
            fence = opener
            continue
        kept, i = [], 0
        while i < len(line):
            if in_comment:
                end = line.find("-->", i)
                if end < 0:
                    i = len(line)
                else:
                    in_comment, i = False, end + 3
                continue
            tick, comment = line.find("`", i), line.find("<!--", i)
            if comment >= 0 and (tick < 0 or comment < tick):
                starts_line = not line[:comment].strip() and indent(line) <= 3
                if starts_line or line.find("-->", comment + 4) >= 0:
                    kept.append(line[i:comment])
                    in_comment, i = True, comment + 4
                else:
                    kept.append(line[i : comment + 4])
                    i = comment + 4
            elif tick >= 0 and (close := line.find("`", tick + 1)) >= 0:
                kept.append(line[i:close + 1])
                i = close + 1
            else:
                kept.append(line[i:])
                i = len(line)
        out.append("".join(kept))
    return out


def heading(line: str) -> str | None:
    """The text of a level-2 or level-3 ATX heading, or None. Plain string operations, no backtracking."""
    rest = line.lstrip(" ")
    if len(line) - len(rest) > 3:
        return None
    level = len(rest) - len(rest.lstrip("#"))
    if level not in (2, 3) or rest[level : level + 1] not in (" ", "\t"):
        return None
    text = rest[level:].strip()
    closing = text.rstrip("#")
    if closing != text and (not closing or closing[-1] in " \t"):
        text = closing.strip()
    return text


def sections(body: str) -> dict[str, str]:
    """Section heading (case-insensitive key) -> its visible text. A repeated heading keeps the first."""
    found: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in [*visible_lines(body), "## "]:
        name = heading(line)
        if name is None:
            lines.append(line)
            continue
        if current is not None:
            found.setdefault(current, "\n".join(lines).strip())
        current, lines = name.lower(), []
    return found


def is_placeholder(text: str) -> bool:
    return text.strip().strip(".").strip().lower() in PLACEHOLDERS


def research_only(listing: str, changed_files: int) -> bool:
    """Whether every changed file, old and new path of a rename, is under research/. False (the full form) when the
    listing may be incomplete: GitHub lists at most MAX_LISTED files, and a shorter list than the PR's count."""
    lines = [line for line in listing.splitlines() if line]
    if not lines or changed_files >= MAX_LISTED or len(lines) < changed_files:
        return False
    for line in lines:
        filename, _, previous = line.partition("\t")
        if not filename.startswith(RESEARCH_PREFIX) or (previous and not previous.startswith(RESEARCH_PREFIX)):
            return False
    return True


def has_issue(text: str) -> bool:
    reason = any(not is_placeholder(m.group(0).split(":", 1)[1]) for m in NO_ISSUE.finditer(text))
    return bool(ISSUE.search(text) or reason)


def check_title(title: str) -> list[str]:
    title = title.strip()
    errors = []
    if not TITLE.match(title):
        errors.append(
            f"Title {title!r} is not a Conventional Commits title: use '<type>: <summary>' or '<type>(<scope>): "
            f"<summary>' with type one of {', '.join(TYPES)}."
        )
    if len(title) > TITLE_MAX:
        errors.append(f"Title is {len(title)} characters; keep it at most {TITLE_MAX}.")
    return errors


def check_research(title: str, body: str) -> list[str]:
    """The research/ form: the title is the benchmark and what was measured, in any style; the description is free
    but must say something besides the issue reference."""
    title = title.strip()
    errors = []
    if is_placeholder(title):
        errors.append("Title is empty; name the benchmark and what the PR measures.")
    elif len(title) > TITLE_MAX:
        errors.append(f"Title is {len(title)} characters; keep it at most {TITLE_MAX}.")
    text = "\n".join(visible_lines(body)).strip()
    if not has_issue(text):
        errors.append("Description: write 'Refs #<number>' with the task's issue (or 'Closes #<number>'), or "
                      "'No issue: <reason>'.")
    rest = ISSUE.sub("", NO_ISSUE.sub("", text)).strip()
    if is_placeholder(rest) or len(rest) < NARRATIVE_MIN:
        errors.append("Description: say what the PR adds or changes and the result, not only the issue reference.")
    return errors


def check_body(body: str, docs_only: bool) -> list[str]:
    found = sections(body)
    required = DOCS_SECTIONS if docs_only else SECTIONS
    errors = []
    for name in required:
        key = name.lower()
        if key not in found:
            errors.append(f"Missing section '## {name}' (from .github/pull_request_template.md).")
            continue
        text = found[key]
        if name == "Scope":
            if not CHECKED.search(text):
                errors.append("Section 'Scope': tick at least one box.")
        elif name == "Related issue":
            if not has_issue(text):
                errors.append("Section 'Related issue': write 'Refs #<number>' (or 'Closes #<number>'), or "
                              "'No issue: <reason>'.")
        elif is_placeholder(text):
            errors.append(f"Section '{name}' is empty or a placeholder.")
        elif name in NARRATIVE and len(text) < NARRATIVE_MIN:
            errors.append(f"Section '{name}' is too short to describe anything ({len(text)} characters).")
    return errors


def check(title: str, body: str, number: int | None, research: bool = False) -> Result:
    if research:
        errors = tuple(check_research(title, body))
    else:
        # The short form needs both a docs title and the ticked "Documentation only" box, so a title alone cannot
        # relax it.
        docs_only = title.strip().startswith(("docs:", "docs(")) and DOCS_BOX.search(sections(body).get("scope", ""))
        errors = tuple(check_title(title) + check_body(body, bool(docs_only)))
    enforced = number is None or number >= FIRST_ENFORCED_PR
    return Result(errors, enforced)


def read_research(path: str | None, raw_count: str | None) -> bool:
    """Whether the PR changes only research/, from the PR_FILES listing. No listing: the full form."""
    if not path:
        return False
    if raw_count is None or not raw_count.isdigit():
        raise SystemExit(f"CHANGED_FILES must be a non-negative integer, got {raw_count!r}")
    with open(path, encoding="utf-8") as f:
        return research_only(f.read(), int(raw_count))


def annotation(level: str, message: str) -> str:
    """One GitHub workflow-command line. The message is data: '%', CR and LF are escaped as GitHub requires, so text
    from the PR can never start a second workflow command on a new line."""
    escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::{level}::{escaped}"


def parse_number(raw: str | None) -> int | None:
    if raw is None or raw == "":
        return None
    if not raw.isdigit():
        raise SystemExit(f"PR_NUMBER must be a positive integer, got {raw!r}")
    return int(raw)


def main() -> int:
    title = os.environ.get("PR_TITLE", "")
    body = os.environ.get("PR_BODY") or ""
    research = read_research(os.environ.get("PR_FILES"), os.environ.get("CHANGED_FILES"))
    result = check(title, body, parse_number(os.environ.get("PR_NUMBER")), research)
    if research:
        print("The PR changes only research/: checked in the research form (title, description, issue reference).")
    level = "error" if result.enforced else "notice"
    for e in result.errors:
        print(annotation(level, e))
    if not result.errors:
        print("PR title and description follow the policy.")
    elif not result.enforced:
        print(f"PR predates the policy (number < {FIRST_ENFORCED_PR}): reported as notices, not enforced.")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
