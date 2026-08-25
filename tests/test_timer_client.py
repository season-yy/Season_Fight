import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMER_JS = PROJECT_ROOT / "static" / "js" / "timer.js"


class TimerClientStateTests(unittest.TestCase):
    def test_pause_waits_for_server_confirmation_before_resume_is_allowed(self):
        source = TIMER_JS.read_text(encoding="utf-8")

        self.assertIn("isRequestPending: false", source)
        self.assertIn("async pause()", source)
        self.assertIn(
            "const data = await api(`/api/timer/pause/${this.currentTask.id}`",
            source,
        )
        self.assertIn("this.currentTask = data.task;", source)


if __name__ == "__main__":
    unittest.main()
