"""Tests for the unassign decision. Run: python .github/scripts/test_board_unassign.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from board_unassign import assignees_to_remove  # noqa: E402

CHANGED = "2026-11-01T12:00:00Z"


class AssigneesToRemove(unittest.TestCase):
    def test_assigned_before_change_is_removed(self):
        events = [("ala", "2026-10-30T09:00:00Z")]
        self.assertEqual(assignees_to_remove("Review", CHANGED, ["ala"], events), ["ala"])

    def test_assigned_after_change_stays(self):
        events = [("ala", "2026-10-30T09:00:00Z"), ("rev", "2026-11-01T12:05:00Z")]
        self.assertEqual(assignees_to_remove("Independent Check", CHANGED, ["ala", "rev"], events), ["ala"])

    def test_reassigned_after_change_stays(self):
        events = [("ala", "2026-10-30T09:00:00Z"), ("ala", "2026-11-01T13:00:00Z")]
        self.assertEqual(assignees_to_remove("Review", CHANGED, ["ala"], events), [])

    def test_other_status_changes_nothing(self):
        events = [("ala", "2026-10-30T09:00:00Z")]
        for status in ("Backlog", "Ready", "In Progress", "Done", None):
            self.assertEqual(assignees_to_remove(status, CHANGED, ["ala"], events), [])

    def test_reversed_event_order_gives_same_result(self):
        events = [
            ("ala", "2026-10-30T09:00:00Z"),
            ("ala", "2026-11-01T13:00:00Z"),
            ("bob", "2026-10-29T09:00:00Z"),
            ("rev", "2026-11-01T12:30:00Z"),
        ]
        forward = assignees_to_remove("Review", CHANGED, ["rev", "bob", "ala"], events)
        backward = assignees_to_remove("Review", CHANGED, ["ala", "bob", "rev"], list(reversed(events)))
        self.assertEqual(forward, ["bob"])
        self.assertEqual(backward, forward)

    def test_assignee_without_event_is_removed(self):
        self.assertEqual(assignees_to_remove("Review", CHANGED, ["old"], []), ["old"])


if __name__ == "__main__":
    unittest.main()
