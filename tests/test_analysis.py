import unittest

from rewindpy.analysis import analyze_crash


class CrashAnalysisTests(unittest.TestCase):
    def test_finds_removed_key_and_probable_rename(self):
        events = [
            {
                "step": 7,
                "event": "line",
                "file": "app.py",
                "line": 4,
                "change_line": 3,
                "function": "normalize_user",
                "changes": {
                    "normalized": {
                        "before": {"user_id": "1024", "name": "Alex"},
                        "after": {"userid": "1024", "name": "Alex"},
                    }
                },
            },
            {
                "step": 12,
                "event": "exception",
                "file": "app.py",
                "line": 8,
                "function": "create_account",
                "changes": {},
            },
        ]
        crash = {"exception_type": "KeyError", "message": "'user_id'"}

        result = analyze_crash(events, crash)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["origin_step"], 7)
        self.assertEqual(result["line"], 3)
        self.assertEqual(result["likely_replacement"], "userid")
        self.assertEqual(result["steps_before_crash"], 5)

    def test_ignores_other_exception_types(self):
        result = analyze_crash([], {"exception_type": "TypeError", "message": "bad"})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
