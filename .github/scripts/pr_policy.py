"""Structural check of a pull request's title and description against .github/pull_request_template.md.

It checks structure only: a Conventional Commits title, the required sections, real content in them (an HTML comment
or a placeholder does not count), at least one ticked scope box, and an issue reference or a stated reason for none.
It does not judge whether the change is good; reviewers do.

Input comes from environment variables, never from the command line, so untrusted text never passes through a shell:
PR_TITLE, PR_BODY, PR_NUMBER. Exit code 0 when the PR passes (or predates the policy), 1 otherwise.

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

ISSUE = re.compile(r"\b(?:Refs|Closes|Fixes|Resolves):? #\d+\b", re.IGNORECASE)
NO_ISSUE = re.compile(r"^No issue: *(?!<)\S.{4,}", re.IGNORECASE | re.MULTILINE)
CHECKED = re.compile(r"^\s*[-*] \[[xX]\] ", re.MULTILINE)
COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
FENCE = re.compile(r"^ {0,3}(```|~~~).*?^ {0,3}\1[^\n]*$", re.DOTALL | re.MULTILINE)
INLINE_CODE = re.compile(r"`[^`\n]*`")
HEADING = re.compile(r"^#{2,3} +(.+?) *#* *$", re.MULTILINE)


@dataclass(frozen=True)
class Result:
    errors: tuple[str, ...]
    enforced: bool

    @property
    def passed(self) -> bool:
        return not self.errors or not self.enforced


def sections(body: str) -> dict[str, str]:
    """Section heading (case-insensitive key) -> its text without HTML comments. A repeated heading keeps the first.

    Code is masked first, so a heading or a "<!--" inside a code block or inline code is text, not structure. A masked
    span still counts as content.
    """
    text = body.replace("\r\n", "\n")
    text = FENCE.sub("[code]", text)
    text = INLINE_CODE.sub("[code]", text)
    text = COMMENT.sub("", text)
    found: dict[str, str] = {}
    matches = list(HEADING.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        found.setdefault(m.group(1).strip().lower(), text[m.end() : end].strip())
    return found


def is_placeholder(text: str) -> bool:
    return text.strip().strip(".").strip().lower() in PLACEHOLDERS


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
            reason = NO_ISSUE.search(text)
            if reason and is_placeholder(reason.group(0).split(":", 1)[1]):
                reason = None
            if not (ISSUE.search(text) or reason):
                errors.append("Section 'Related issue': write 'Refs #<number>' (or 'Closes #<number>'), or "
                              "'No issue: <reason>'.")
        elif is_placeholder(text):
            errors.append(f"Section '{name}' is empty or a placeholder.")
        elif name in NARRATIVE and len(text) < NARRATIVE_MIN:
            errors.append(f"Section '{name}' is too short to describe anything ({len(text)} characters).")
    return errors


def check(title: str, body: str, number: int | None) -> Result:
    docs_only = title.strip().startswith(("docs:", "docs("))
    errors = tuple(check_title(title) + check_body(body, docs_only))
    enforced = number is None or number >= FIRST_ENFORCED_PR
    return Result(errors, enforced)


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
    result = check(title, body, parse_number(os.environ.get("PR_NUMBER")))
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
