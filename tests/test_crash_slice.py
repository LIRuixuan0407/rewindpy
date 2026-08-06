import unittest

from rewindpy.analysis import build_crash_slice


class CrashSliceTests(unittest.TestCase):
    def test_keeps_recent_context_traceback_checkpoints_and_origin(self):
        events = []
        for step in range(1, 101):
            function = "background"
            event_type = "line"
            line = step
            exception_type = None

            if step == 8:
                function = "handle_request"
                event_type = "call"
                line = 10
            elif step == 20:
                function = "normalize"
                line = 22
            elif step == 69:
                function = "create_account"
                event_type = "call"
                line = 30
            elif step >= 70:
                function = "create_account"
                line = 40
            if step == 100:
                event_type = "exception"
                exception_type = "KeyError"

            events.append(
                {
                    "step": step,
                    "event": event_type,
                    "file": "app.py",
                    "line": line,
                    "function": function,
                    "exception_type": exception_type,
                }
            )

        crash = {
            "exception_type": "KeyError",
            "file": "app.py",
            "line": 40,
            "function": "create_account",
            "traceback": [
                {
                    "file": "app.py",
                    "line": 10,
                    "function": "handle_request",
                    "project_file": True,
                },
                {
                    "file": "app.py",
                    "line": 40,
                    "function": "create_account",
                    "project_file": True,
                },
            ],
        }
        analysis = {"origin_step": 20}

        result = build_crash_slice(events, crash, analysis, context_steps=10)

        self.assertEqual(result["total_events"], 100)
        self.assertLess(result["shown_events"], result["total_events"])
        self.assertIn(8, result["steps"])
        self.assertIn(19, result["steps"])
        self.assertIn(20, result["steps"])
        self.assertIn(21, result["steps"])
        self.assertIn(69, result["steps"])
        self.assertIn(91, result["steps"])
        self.assertIn(100, result["steps"])
        self.assertNotIn(1, result["steps"])
        self.assertNotIn(50, result["steps"])

    def test_falls_back_to_last_event_without_exception(self):
        events = [
            {
                "step": step,
                "event": "line",
                "file": "app.py",
                "line": step,
                "function": "main",
            }
            for step in range(1, 6)
        ]

        result = build_crash_slice(events, {}, context_steps=2)

        self.assertEqual(result["steps"], [4, 5])
        self.assertEqual(result["anchor_step"], 5)

    def test_empty_events_returns_empty_slice(self):
        result = build_crash_slice([], {}, context_steps=30)

        self.assertEqual(result["steps"], [])
        self.assertEqual(result["shown_events"], 0)
        self.assertEqual(result["omitted_events"], 0)


if __name__ == "__main__":
    unittest.main()
