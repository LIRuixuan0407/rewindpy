import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from rewindpy import __version__
from rewindpy.cli import main


class CliTests(unittest.TestCase):
    def test_version(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn(__version__, output.getvalue())

    def test_demo_generates_report_and_returns_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "demo.html"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["demo", "none-origin", "--output", str(report)])
            self.assertEqual(code, 0)
            self.assertTrue(report.is_file())
            html = report.read_text(encoding="utf-8")
            self.assertIn("None value traced", html)
            self.assertIn("Crash Slice", html)

    def test_doctor_reports_ready(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--lang", "en", "doctor"])
        self.assertEqual(code, 0)
        self.assertIn("Status: READY", output.getvalue())
        self.assertIn("Built-in demo smoke test: PASS", output.getvalue())

    def test_doctor_supports_json_output(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["doctor", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"ready": true', output.getvalue())
        self.assertIn('"demo_smoke_test": true', output.getvalue())


if __name__ == "__main__":
    unittest.main()
