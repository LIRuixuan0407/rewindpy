import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from rewindpy.cli import main
from rewindpy.i18n import normalize_language


class InternationalizationTests(unittest.TestCase):
    def test_language_aliases(self):
        self.assertEqual(normalize_language("zh-CN"), "zh")
        self.assertEqual(normalize_language("English"), "en")

    def test_chinese_help_can_be_selected_after_subcommand(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stdout(output):
            main(["demo", "--help", "--lang", "zh"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("生成内置崩溃演示报告", output.getvalue())
        self.assertIn("在浏览器中打开报告", output.getvalue())

    def test_chinese_demo_contains_both_report_languages(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "demo.html"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(
                    [
                        "--lang",
                        "zh",
                        "demo",
                        "none-origin",
                        "--output",
                        str(report),
                    ]
                )
            self.assertEqual(code, 0)
            html = report.read_text(encoding="utf-8")
            self.assertIn("已追踪 None 来源", html)
            self.assertIn("None value traced", html)
            self.assertIn("崩溃切片", html)
            self.assertIn('id="langZh"', html)

    def test_chinese_doctor(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["doctor", "--lang=zh"])
        self.assertEqual(code, 0)
        self.assertIn("RewindPy 环境诊断", output.getvalue())
        self.assertIn("内置演示冒烟测试: 通过", output.getvalue())


if __name__ == "__main__":
    unittest.main()
