"""Static invariants of .github/CODEOWNERS. This is not a check of live permissions.

What this file can check offline: every rule has an owner, every owner is one recorded below as verified, owners are
spelled as GitHub expects, and literal paths exist. What it cannot check: that the team still exists, still has write
access, or has members, or that GitHub parses the file the same way. GitHub's own parser checks the first two and the
syntax on every PR (`CODEOWNERS validation` job in .github/workflows/repo-checks.yml, via the codeowners/errors API).
Whether an owner's approval is required at all is a ruleset setting, which neither check can see.

Run: python3 -m unittest discover -s .github/scripts -p "test_codeowners.py"
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CODEOWNERS = REPO / ".github" / "CODEOWNERS"

VERIFIED_OWNERS = {"@slayerlabs/benchmark-reviewers"}
"""Recorded after `gh api repos/slayerlabs/benchmarks-fabryka-ai/teams` on 2026-11-19 showed the team with write
("push") access. A new owner is added here in the same reviewed PR that adds it to CODEOWNERS, so adding an owner is
always a visible, deliberate change."""


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

    def test_owners_are_recorded_as_verified(self) -> None:
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

    def test_live_validation_job_wiring(self) -> None:
        # A literal wiring guard on the YAML, not a behavior test: the behavior was checked on GitHub (PR description).
        workflow = (REPO / ".github" / "workflows" / "repo-checks.yml").read_text(encoding="utf-8")
        self.assertIn("codeowners/errors?ref=refs/pull/$PR/merge", workflow)
        self.assertIn('[ "$errors" = "[]" ]', workflow)
        self.assertIn("::error::GitHub found no CODEOWNERS file", workflow)  # 404 fails with a message


if __name__ == "__main__":
    unittest.main()
