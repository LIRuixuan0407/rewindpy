import tempfile
import unittest
from pathlib import Path

from rewindpy.runner import run_target


class RunnerTests(unittest.TestCase):
    def test_crash_creates_report_and_redacts_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "boom.py"
            report = root / "report.html"
            script.write_text(
                'api_key = "super-secret"\nvalue = {"x": 1}\nprint(value["missing"])\n',
                encoding="utf-8",
            )
            code = run_target(script, [], output=report, max_events=100)
            self.assertEqual(code, 1)
            self.assertTrue(report.exists())
            html = report.read_text(encoding="utf-8")
            self.assertIn("KeyError", html)
            self.assertNotIn("super-secret", html)
            self.assertIn("<redacted>", html)

    def test_success_does_not_create_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "ok.py"
            report = root / "report.html"
            script.write_text('print("ok")\n', encoding="utf-8")
            code = run_target(script, [], output=report)
            self.assertEqual(code, 0)
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
