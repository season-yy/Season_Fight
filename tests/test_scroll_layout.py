import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_CSS = PROJECT_ROOT / "static" / "css" / "main.css"
SERVICE_WORKER = PROJECT_ROOT / "static" / "sw.js"


class DesktopScrollLayoutTests(unittest.TestCase):
    def test_desktop_uses_document_scrolling_instead_of_nested_scroll_area(self):
        css = MAIN_CSS.read_text(encoding="utf-8")
        desktop_rules = css.split("@media (min-width: 768px)", 1)[1].split(
            "@media (min-width: 1200px)", 1
        )[0]
        app_main_rules = desktop_rules.split(".app-main {", 1)[1].split("}", 1)[0]

        self.assertIn("overflow-y: auto", desktop_rules)
        self.assertNotIn("height: calc(100vh - 56px)", app_main_rules)
        self.assertNotIn("overflow-y: auto", app_main_rules)

    def test_new_scroll_css_is_not_hidden_by_the_previous_static_cache(self):
        service_worker = SERVICE_WORKER.read_text(encoding="utf-8")
        self.assertIn("season-fight-v3", service_worker)


if __name__ == "__main__":
    unittest.main()
