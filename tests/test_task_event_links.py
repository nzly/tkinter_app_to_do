import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.db import get_task_event_ids, init_db, insert_task, update_task
from objects.data_objects import TaskItem


class TaskEventLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.db")
        init_db(self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            for event_id in (101, 102):
                conn.execute(
                    """
                    INSERT INTO calendar_events (
                        id, title, start_at, end_at, is_all_day, created_at, created_by_user
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (event_id, f"Event {event_id}", "2026-10-17", "2026-10-17", 1, "2026-10-17", 1),
                )

        self.task = insert_task(
            self.db_path,
            TaskItem(task_id=0, task_name="Test task", created_by_user=1),
            event_ids=[101],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_update_replaces_event_links(self) -> None:
        updated_task = TaskItem(task_id=self.task.task_id, task_name="Updated task", created_by_user=1)

        self.assertTrue(update_task(self.db_path, updated_task, event_ids=[102]))
        self.assertEqual(get_task_event_ids(self.db_path, self.task.task_id), [102])

        self.assertTrue(update_task(self.db_path, updated_task, event_ids=[]))
        self.assertEqual(get_task_event_ids(self.db_path, self.task.task_id), [])

    def test_update_without_event_ids_preserves_existing_links(self) -> None:
        updated_task = TaskItem(task_id=self.task.task_id, task_name="Updated task", created_by_user=1)

        self.assertTrue(update_task(self.db_path, updated_task))
        self.assertEqual(get_task_event_ids(self.db_path, self.task.task_id), [101])


if __name__ == "__main__":
    unittest.main()