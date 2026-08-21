import importlib.machinery
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STOP_SCRIPT = PROJECT_ROOT / "stop.pyw"


def load_launcher():
    loader = importlib.machinery.SourceFileLoader(
        "season_fight_launcher", str(PROJECT_ROOT / "start_app.pyw")
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_stop_script():
    loader = importlib.machinery.SourceFileLoader(
        "season_fight_stopper", str(STOP_SCRIPT)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class DesktopShortcutTests(unittest.TestCase):
    def test_uses_windows_reported_desktop_directory(self):
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop = Path(temp_dir) / "桌面"
            desktop.mkdir()
            with patch.object(launcher, "_get_windows_desktop_path", return_value=desktop):
                self.assertEqual(launcher.get_desktop_path(), desktop)

    def test_records_started_backend_pid_for_the_stop_script(self):
        launcher = load_launcher()
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_file = Path(temp_dir) / "state" / "server.pid"
            with patch.object(launcher, "PID_FILE", pid_file):
                launcher.save_server_pid(4321)

            self.assertEqual(pid_file.read_text(encoding="utf-8"), "4321")


class StopScriptSafetyTests(unittest.TestCase):
    def test_stops_a_recorded_process_instead_of_all_pythonw_processes(self):
        source = STOP_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("def stop_server", source)
        self.assertNotIn('"/IM", "pythonw.exe"', source)

    def test_stops_only_the_pid_saved_by_the_launcher(self):
        stopper = load_stop_script()
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_file = Path(temp_dir) / "server.pid"
            pid_file.write_text("4321", encoding="utf-8")
            completed = subprocess.CompletedProcess([], 0)
            with (
                patch.object(stopper, "PID_FILE", pid_file),
                patch.object(stopper.subprocess, "run", return_value=completed) as run,
            ):
                stopped, _ = stopper.stop_server()

            self.assertTrue(stopped)
            self.assertFalse(pid_file.exists())
            run.assert_called_once_with(
                ["taskkill", "/F", "/PID", "4321", "/T"],
                creationflags=stopper.CREATE_NO_WINDOW,
                capture_output=True,
                timeout=5,
            )


if __name__ == "__main__":
    unittest.main()
