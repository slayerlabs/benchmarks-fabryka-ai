"""CODEOWNERS names only owners verified to exist with write access, and only paths that exist.

GitHub silently ignores an owner it cannot resolve, so a typo or an invented team would leave a path unowned while the
file suggests otherwise. Run: python3 -m unittest discover -s .github/scripts -p "test_codeowners.py"
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CODEOWNERS = REPO / ".github" / "CODEOWNERS"

VERIFIED_OWNERS = {"@slayerlabs/benchmark-reviewers"}
"""Checked with `gh api repos/slayerlabs/benchmarks-fabryka-ai/teams` on 2026-11-19: the team exists and has write
("push") access. Add an owner here only in the same reviewed PR that verifies it the same way."""


def rules() -> list[tuple[str, list[str]]]:
    out = []
    for line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pattern, *owners = line.split()
            out.append((pattern, owners))
    return out


class Codeowners(unittest.TestCase):
    def test_every_rule_has_owners(self) -> None:
        self.assertTrue(rules())
        for pattern, owners in rules():
            self.assertTrue(owners, f"{pattern} has no owner; leave unowned paths as comments instead")

    def test_owners_are_verified(self) -> None:
        for pattern, owners in rules():
            self.assertLessEqual(set(owners), VERIFIED_OWNERS, pattern)

    def test_owner_syntax(self) -> None:
        for _, owners in rules():
            for owner in owners:
                self.assertRegex(owner, r"^@[A-Za-z0-9-]+(/[A-Za-z0-9-]+)?$")

    def test_literal_paths_exist(self) -> None:
        for pattern, _ in rules():
            if not re.search(r"[*?\[]", pattern):
                self.assertTrue((REPO / pattern.strip("/")).exists(), pattern)


if __name__ == "__main__":
    unittest.main()
