import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from core import task_manager


class PausedTimerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tasks_dir = Path(self.temp_dir.name) / "tasks"
        self.plans_dir = Path(self.temp_dir.name) / "plans"
        self.archive_dir = Path(self.temp_dir.name) / "archive"
        self.path_patches = [
            patch.object(task_manager, "TASKS_DIR", self.tasks_dir),
            patch.object(task_manager, "PLANS_DIR", self.plans_dir),
            patch.object(task_manager, "ARCHIVE_DIR", self.archive_dir),
        ]
        for item in self.path_patches:
            item.start()

        self.today = datetime.now().strftime("%Y-%m-%d")

    def tearDown(self):
        for item in reversed(self.path_patches):
            item.stop()
        self.temp_dir.cleanup()

    def make_paused_task(self):
        task = task_manager.create_task("恢复测试", "测试", date=self.today)
        data = task_manager.load_day(self.today)
        stored_task = data["tasks"][0]
        stored_task.update(
            status="paused",
            duration_seconds=90,
            started_at=None,
            paused_at=datetime.now().isoformat(timespec="seconds"),
        )
        task_manager.save_day(self.today, data)
        return task["id"]

    def test_resuming_a_paused_task_does_not_count_the_break(self):
        task_id = self.make_paused_task()

        with patch.object(task_manager, "_elapsed_since", return_value=60):
            resumed = task_manager.start_task(task_id)

        self.assertEqual(resumed["status"], "running")
        self.assertEqual(resumed["duration_seconds"], 90)
        self.assertIsNone(resumed["paused_at"])

    def test_completing_a_paused_task_does_not_count_the_break(self):
        task_id = self.make_paused_task()

        with patch.object(task_manager, "_elapsed_since", return_value=60):
            completed = task_manager.complete_task(task_id)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["duration_seconds"], 90)


if __name__ == "__main__":
    unittest.main()
