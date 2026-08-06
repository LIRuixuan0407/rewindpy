import json
import re
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

    def test_keyerror_report_contains_value_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "rename.py"
            report = root / "report.html"
            script.write_text(
                "def normalize(data):\n"
                "    result = dict(data)\n"
                "    result['userid'] = result.pop('user_id')\n"
                "    return result\n\n"
                "cleaned = normalize({'user_id': '42'})\n"
                "print(cleaned['user_id'])\n",
                encoding="utf-8",
            )

            code = run_target(script, [], output=report, max_events=100)

            self.assertEqual(code, 1)
            html = report.read_text(encoding="utf-8")
            match = re.search(
                r'<script id="rewind-data" type="application/json">(.*?)</script>',
                html,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            assert match is not None
            payload = json.loads(match.group(1))
            analysis = payload["analysis"]
            self.assertEqual(analysis["missing_key"], "user_id")
            self.assertEqual(analysis["likely_replacement"], "userid")
            self.assertEqual(analysis["line"], 3)


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
