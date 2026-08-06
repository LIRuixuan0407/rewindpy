import json
import re
import tempfile
import unittest
from pathlib import Path

from rewindpy.runner import run_target
from rewindpy.tracer import RewindTracer


class SafeTracingTests(unittest.TestCase):
    def test_ring_buffer_keeps_latest_events_and_counts_discarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "loop.py"
            report = root / "report.html"
            script.write_text(
                "value = 0\nfor index in range(200):\n    value += index\nraise RuntimeError('boom')\n",
                encoding="utf-8",
            )
            code = run_target(script, [], output=report, max_events=25)
            self.assertEqual(code, 1)
            html = report.read_text(encoding="utf-8")
            match = re.search(r'<script id="rewind-data" type="application/json">(.*?)</script>', html, re.DOTALL)
            self.assertIsNotNone(match)
            payload = json.loads(match.group(1))
            stats = payload["trace_stats"]
            self.assertLessEqual(stats["retained_events"], 25)
            self.assertGreater(stats["discarded_events"], 0)
            self.assertTrue(any(event["exception_type"] == "RuntimeError" for event in payload["events"]))

    def test_exclude_path_skips_nested_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            excluded = root / "generated"
            excluded.mkdir()
            tracer = RewindTracer(root, exclude_paths=[excluded])
            self.assertFalse(tracer._is_project_file(str(excluded / "module.py")))
            self.assertTrue(tracer._is_project_file(str(root / "app.py")))

    def test_include_path_limits_trace_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            included = root / "src"
            included.mkdir()
            tracer = RewindTracer(root, include_paths=[included])
            self.assertTrue(tracer._is_project_file(str(included / "module.py")))
            self.assertFalse(tracer._is_project_file(str(root / "tests" / "test_app.py")))


if __name__ == "__main__":
    unittest.main()
