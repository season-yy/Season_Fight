import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_launcher():
    loader = importlib.machinery.SourceFileLoader(
        "season_fight_launcher", str(PROJECT_ROOT / "start_app.pyw")
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


if __name__ == "__main__":
    unittest.main()
