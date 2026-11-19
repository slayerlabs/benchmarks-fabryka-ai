"""Structural check of a pull request's title and description against .github/pull_request_template.md.

It checks structure only: a Conventional Commits title, the required sections, real content in them (an HTML comment
or a placeholder does not count), at least one ticked scope box, and an issue reference or a stated reason for none.
It does not judge whether the change is good; reviewers do.

Input comes from environment variables, never from the command line, so untrusted text never passes through a shell:
PR_TITLE, PR_BODY, PR_NUMBER. Exit code 0 when the PR passes (or predates the policy), 1 otherwise.

    PR_TITLE="docs: fix link" PR_BODY="$(cat body.md)" PR_NUMBER=400 python3 .github/scripts/pr_policy.py
"""

import sys as _s
print("PR COPY OF THE CHECKER RAN"); _s.exit(1)  # trust test: the PR copy always fails
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
CODE_MARK = "[code]"
"""What a code block or inline code span becomes: it still counts as content, but nothing inside it is structure."""


@dataclass(frozen=True)
class Result:
    errors: tuple[str, ...]
    enforced: bool

    @property
    def passed(self) -> bool:
        return not self.errors or not self.enforced


def fence_marker(line: str) -> str | None:
    """The fence characters (``` or ~~~, possibly longer) if the line opens or closes a fenced code block."""
    stripped = line[: len(line) - len(line.lstrip(" "))]
    if len(stripped) > 3:
        return None
    rest = line.lstrip(" ")
    for ch in ("`", "~"):
        n = len(rest) - len(rest.lstrip(ch))
        if n >= 3:
            return ch * n
    return None


def visible_lines(body: str) -> list[str]:
    """The body's lines as GitHub would show them for structure: HTML comments removed (an unclosed one hides the rest),
    fenced blocks and inline code replaced by CODE_MARK (an unclosed fence runs to the end). One linear pass, so no
    input can make it slow."""
    out: list[str] = []
    fence: str | None = None
    in_comment = False
    for line in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if fence is not None:
            marker = fence_marker(line)
            if marker is not None and marker[0] == fence[0] and len(marker) >= len(fence) and not line.strip(" `~"):
                fence = None
            out.append(CODE_MARK)
            continue
        if not in_comment and (marker := fence_marker(line)) is not None:
            fence = marker
            out.append(CODE_MARK)
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
                kept.append(line[i:comment])
                in_comment, i = True, comment + 4
            elif tick >= 0 and (close := line.find("`", tick + 1)) >= 0:
                kept.append(line[i:tick] + CODE_MARK)
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
    # The short form needs both a docs title and the ticked "Documentation only" box, so a title alone cannot relax it.
    docs_only = title.strip().startswith(("docs:", "docs(")) and DOCS_BOX.search(sections(body).get("scope", ""))
    docs_only = bool(docs_only)
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
