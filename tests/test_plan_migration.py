import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app import app
from core import task_manager


class DuePlanMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_root = Path(self.temp_dir.name)
        self.tasks_dir = temp_root / "tasks"
        self.plans_dir = temp_root / "plans"
        self.archive_dir = temp_root / "archive"
        self.path_patches = [
            patch.object(task_manager, "TASKS_DIR", self.tasks_dir),
            patch.object(task_manager, "PLANS_DIR", self.plans_dir),
            patch.object(task_manager, "ARCHIVE_DIR", self.archive_dir),
        ]
        for item in self.path_patches:
            item.start()

        self.today = datetime.now().strftime("%Y-%m-%d")
        planned_task = task_manager.make_task(
            "今天应可开始的计划", "测试", self.today, is_planned=True
        )
        task_manager.save_plan(self.today, {"date": self.today, "tasks": [planned_task]})
        app.config.update(TESTING=True)

    def tearDown(self):
        for item in reversed(self.path_patches):
            item.stop()
        self.temp_dir.cleanup()

    def test_reading_today_tasks_migrates_due_plans_when_midnight_job_was_missed(self):
        response = app.test_client().get(f"/api/tasks?date={self.today}")

        self.assertEqual(response.status_code, 200)
        tasks = response.get_json()["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["name"], "今天应可开始的计划")
        self.assertFalse(tasks[0]["is_planned"])
        self.assertEqual(tasks[0]["status"], "pending")
        self.assertFalse((self.plans_dir / f"{self.today}.json").exists())


if __name__ == "__main__":
    unittest.main()
