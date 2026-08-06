import unittest

from rewindpy.analysis import analyze_crash, build_crash_slice


class NoneOriginTests(unittest.TestCase):
    def test_finds_function_returning_none(self):
        events = [
            {
                "step": 4,
                "event": "return",
                "file": "app.py",
                "line": 5,
                "function": "find_user",
                "depth": 4,
                "return_value": None,
                "locals": {},
                "changes": {},
            },
            {
                "step": 5,
                "event": "line",
                "file": "app.py",
                "line": 9,
                "change_line": 8,
                "function": "<module>",
                "depth": 3,
                "locals": {"current_user": None},
                "changes": {
                    "current_user": {"before": "<not set>", "after": None}
                },
            },
            {
                "step": 8,
                "event": "exception",
                "file": "app.py",
                "line": 7,
                "function": "render_profile",
                "depth": 4,
                "locals": {"user": None},
                "changes": {},
                "exception_type": "AttributeError",
                "exception_message": "'NoneType' object has no attribute 'get'",
            },
        ]
        crash = {
            "exception_type": "AttributeError",
            "message": "'NoneType' object has no attribute 'get'",
            "file": "app.py",
            "line": 7,
            "function": "render_profile",
            "traceback": [
                {
                    "file": "app.py",
                    "line": 10,
                    "function": "<module>",
                    "source": "render_profile(current_user)",
                    "project_file": True,
                },
                {
                    "file": "app.py",
                    "line": 7,
                    "function": "render_profile",
                    "source": "return user.get('name')",
                    "project_file": True,
                },
            ],
        }

        result = analyze_crash(events, crash)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["kind"], "none-value-origin")
        self.assertEqual(result["variable"], "user")
        self.assertEqual(result["upstream_variable"], "current_user")
        self.assertEqual(result["producer_function"], "find_user")
        self.assertEqual(result["origin_step"], 4)
        self.assertEqual(result["line"], 5)

    def test_finds_direct_none_assignment(self):
        events = [
            {
                "step": 2,
                "event": "line",
                "file": "app.py",
                "line": 3,
                "change_line": 2,
                "function": "<module>",
                "depth": 3,
                "locals": {"user": None},
                "changes": {"user": {"before": "<not set>", "after": None}},
            },
            {
                "step": 3,
                "event": "exception",
                "file": "app.py",
                "line": 3,
                "function": "<module>",
                "depth": 3,
                "locals": {"user": None},
                "changes": {},
                "exception_type": "AttributeError",
            },
        ]
        crash = {
            "exception_type": "AttributeError",
            "message": "'NoneType' object has no attribute 'name'",
            "file": "app.py",
            "line": 3,
            "function": "<module>",
            "traceback": [
                {
                    "file": "app.py",
                    "line": 3,
                    "function": "<module>",
                    "source": "print(user.name)",
                    "project_file": True,
                }
            ],
        }

        result = analyze_crash(events, crash)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["reason"], "assigned-none")
        self.assertEqual(result["origin_step"], 2)
        self.assertEqual(result["line"], 2)

    def test_selects_correct_variable_when_multiple_are_none(self):
        events = [
            {
                "step": 2,
                "event": "line",
                "file": "app.py",
                "line": 4,
                "change_line": 3,
                "function": "<module>",
                "depth": 3,
                "locals": {"config": None, "user": None},
                "changes": {
                    "config": {"before": "<not set>", "after": None},
                    "user": {"before": "<not set>", "after": None},
                },
            },
            {
                "step": 3,
                "event": "exception",
                "file": "app.py",
                "line": 4,
                "function": "<module>",
                "depth": 3,
                "locals": {"config": None, "user": None},
                "changes": {},
                "exception_type": "AttributeError",
            },
        ]
        crash = {
            "exception_type": "AttributeError",
            "message": "'NoneType' object has no attribute 'name'",
            "file": "app.py",
            "line": 4,
            "function": "<module>",
            "traceback": [
                {
                    "file": "app.py",
                    "line": 4,
                    "function": "<module>",
                    "source": "print(user.name)",
                    "project_file": True,
                }
            ],
        }

        result = analyze_crash(events, crash)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["variable"], "user")

    def test_ignores_non_none_attribute_error(self):
        crash = {
            "exception_type": "AttributeError",
            "message": "'User' object has no attribute 'missing'",
        }
        self.assertIsNone(analyze_crash([], crash))

    def test_origin_is_kept_in_crash_slice(self):
        events = [
            {
                "step": step,
                "event": "exception" if step == 40 else "line",
                "file": "app.py",
                "line": step,
                "function": "main",
                "exception_type": "AttributeError" if step == 40 else None,
            }
            for step in range(1, 41)
        ]
        analysis = {"origin_step": 3}
        crash = {
            "exception_type": "AttributeError",
            "file": "app.py",
            "line": 40,
            "function": "main",
            "traceback": [],
        }

        result = build_crash_slice(events, crash, analysis, context_steps=5)

        self.assertIn(3, result["steps"])
        self.assertIn(40, result["steps"])


if __name__ == "__main__":
    unittest.main()
