"""Tests for the stage B+C decision. Run: python .github/scripts/test_stage_bc_after_card.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stage_bc_after_card import card_catalog, decide, marker, stage_bc_body  # noqa: E402

REPO = "slayerlabs/benchmarks-fabryka-ai"


def closed(title, number=200, reason="completed", body=""):
    return {"action": "closed", "issue": {"number": number, "title": title, "state_reason": reason, "body": body}}


class Decide(unittest.TestCase):
    def test_card_title_gives_stage_bc_title(self):
        self.assertEqual(
            decide(closed("Karta oryginału: PAWS (część angielska PAWS-X)"), []),
            ("PAWS (część angielska PAWS-X)",
             "PAWS (część angielska PAWS-X) nie ma wyniku Slayera 1.06 w repo benchmarków"),
        )

    def test_not_planned_creates_nothing(self):
        name, _ = decide(closed("Karta oryginału: COPA", reason="not_planned"), [])
        self.assertIsNone(name)

    def test_other_issue_creates_nothing(self):
        name, _ = decide(closed("Policz PIQA według definicji „zrobione”"), [])
        self.assertIsNone(name)

    def test_existing_hand_written_stage_bc_creates_nothing(self):
        existing = [{"number": 29, "title": "ARC-Challenge nie spełnia definicji „zrobiony” w repo benchmarków"}]
        name, reason = decide(closed("Karta oryginału: ARC-Challenge", number=49), existing)
        self.assertIsNone(name)
        self.assertIn("#29", reason)

    def test_existing_issue_with_marker_creates_nothing(self):
        existing = [{"number": 300, "title": "inny tytuł", "body": "x\n" + marker(200)}]
        name, _ = decide(closed("Karta oryginału: COPA"), existing)
        self.assertIsNone(name)

    def test_existing_issue_starting_after_card_creates_nothing(self):
        existing = [{"number": 23, "title": "coś innego", "body": "Start po merge'u karty oryginału #45."}]
        name, _ = decide(closed("Karta oryginału: ARC-Easy", number=45), existing)
        self.assertIsNone(name)

    def test_longer_benchmark_name_is_not_a_duplicate(self):
        existing = [
            {"number": 33, "title": "BLiMP Supplement nie ma wyniku Slayera 1.06 w repo benchmarków"},
            {"number": 53, "title": "Karta oryginału: BLiMP Supplement"},
            {"number": 1, "title": "PR", "pull_request": {}, "body": marker(200)},
            {"number": 2, "body": "karty oryginału #2001"},
        ]
        name, _ = decide(closed("Karta oryginału: BLiMP"), existing)
        self.assertEqual(name, "BLiMP")


class Catalog(unittest.TestCase):
    def test_single_catalog(self):
        body = "Karta `research/benchmarks/arc-easy/ORIGINAL.md` według wzoru " \
               "[`research/benchmarks/_template/ORIGINAL.md`](x). Potem research/benchmarks/arc-easy/ORIGINAL.md."
        self.assertEqual(card_catalog(body), "arc-easy")

    def test_two_catalogs_or_none_is_unknown(self):
        self.assertIsNone(card_catalog("research/benchmarks/a/ORIGINAL.md i research/benchmarks/b/ORIGINAL.md"))
        self.assertIsNone(card_catalog(None))

    def test_body_without_catalog_links_only_the_card(self):
        body = stage_bc_body(REPO, "COPA", 105, None)
        self.assertIn("#105", body)
        self.assertNotIn("/ORIGINAL.md", body)
        self.assertIn(marker(105), body)

    def test_body_with_catalog_links_original(self):
        body = stage_bc_body(REPO, "ARC-Easy", 45, "arc-easy")
        self.assertIn(f"https://github.com/{REPO}/blob/main/research/benchmarks/arc-easy/ORIGINAL.md", body)
        self.assertNotRegex(body.lower(), r"\bnasz|u nas")


if __name__ == "__main__":
    unittest.main()
