import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from windows.new_task_window import build_repeat_occurrences


class RepeatTaskTests(unittest.TestCase):
    def test_generates_occurrences_for_selected_weekdays(self) -> None:
        start_date = date(2026, 8, 1)  # Saturday
        occurrences = build_repeat_occurrences(start_date, [0, 2], months=0, years=0)
        self.assertIn(date(2026, 8, 3), occurrences)
        self.assertIn(date(2026, 8, 5), occurrences)

    def test_extends_occurrences_to_the_requested_duration(self) -> None:
        start_date = date(2026, 8, 1)  # Saturday
        occurrences = build_repeat_occurrences(start_date, [5], months=1, years=0)
        self.assertIn(date(2026, 8, 1), occurrences)
        self.assertNotIn(date(2026, 10, 2), occurrences)
        self.assertIn(date(2026, 8, 29), occurrences)

    def test_one_month_means_one_month(self) -> None:
        start_date = date(2026, 8, 1)  # Saturday
        occurrences = build_repeat_occurrences(start_date, [5], months=1, years=0)
        self.assertIn(date(2026, 8, 1), occurrences)
        self.assertNotIn(date(2026, 9, 5), occurrences)


if __name__ == "__main__":
    unittest.main()
