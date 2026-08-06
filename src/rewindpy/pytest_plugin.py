from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path
from typing import Any

import pytest

from .i18n import normalize_language
from .runner import _write
from .tracer import RewindTracer, build_crash_info

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("rewindpy", "RewindPy post-failure reports")
    group.addoption(
        "--rewind",
        action="store_true",
        default=False,
        help="Generate a RewindPy report for each failed test / 为每个失败测试生成 RewindPy 报告",
    )
    group.addoption(
        "--rewind-dir",
        default=".rewindpy",
        metavar="PATH",
        help="Report output directory / 报告输出目录",
    )
    group.addoption(
        "--rewind-max-events",
        type=int,
        default=5_000,
        metavar="N",
        help="Maximum retained events per test / 每个测试最多保留的事件数",
    )
    group.addoption(
        "--rewind-max-report-mb",
        type=float,
        default=20.0,
        metavar="MB",
        help="Maximum report size per test / 每个测试的最大报告体积",
    )
    group.addoption(
        "--rewind-lang",
        default="auto",
        choices=("auto", "en", "zh"),
        help="Report language / 报告语言",
    )


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--rewind"):
        config.pluginmanager.register(RewindPyPytestPlugin(config), "rewindpy-runtime")


class RewindPyPytestPlugin:
    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.root = Path(str(config.rootpath)).resolve()
        output = Path(config.getoption("--rewind-dir"))
        self.output_dir = output if output.is_absolute() else self.root / output
        self.max_events = max(10, int(config.getoption("--rewind-max-events")))
        self.max_report_mb = max(0.25, float(config.getoption("--rewind-max-report-mb")))
        self.language = normalize_language(config.getoption("--rewind-lang"))
        self.reports: list[tuple[str, Path]] = []
        self.tests_observed = 0
        self.failed_tests = 0
        self.index_path: Path | None = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: pytest.Item) -> Any:
        tracer = RewindTracer(self.root, max_events=self.max_events)
        tracer.start()
        outcome = yield
        tracer.stop()

        if outcome.excinfo is None:
            return

        exc_type, exc_value, traceback = outcome.excinfo
        crash = build_crash_info(exc_type, exc_value, traceback, self.root)
        report_path = self.output_dir / _report_filename(item.nodeid)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        target = Path(str(getattr(item, "path", item.fspath))).resolve()
        _write(
            report_path,
            tracer,
            crash.to_dict(),
            target,
            [item.nodeid],
            self.language,
            self.max_report_mb,
        )
        self.reports.append((item.nodeid, report_path))

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when != "call":
            return
        self.tests_observed += 1
        if report.failed:
            self.failed_tests += 1

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        del session, exitstatus
        if self.reports:
            self.index_path = self.output_dir / "index.html"
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.index_path.write_text(self._render_index(), encoding="utf-8")

    def pytest_terminal_summary(
        self,
        terminalreporter: pytest.TerminalReporter,
        exitstatus: int,
        config: pytest.Config,
    ) -> None:
        del exitstatus, config
        terminalreporter.section("RewindPy", sep="=")
        if self.language == "zh":
            terminalreporter.write_line(f"✓ 已监控测试：{self.tests_observed}")
            terminalreporter.write_line(f"✗ 失败测试：{self.failed_tests}")
            terminalreporter.write_line(f"📄 已生成报告：{len(self.reports)}")
        else:
            terminalreporter.write_line(f"✓ Tests observed: {self.tests_observed}")
            terminalreporter.write_line(f"✗ Failed tests: {self.failed_tests}")
            terminalreporter.write_line(f"📄 Reports generated: {len(self.reports)}")

        if not self.reports:
            if self.language == "zh":
                terminalreporter.write_line("无需生成报告：所有测试均通过。")
            else:
                terminalreporter.write_line("No reports needed: all tests passed.")
            return

        if self.index_path is not None:
            terminalreporter.write_line(
                self._display_line(
                    "Report index",
                    "报告索引",
                    self.index_path,
                )
            )
        for nodeid, path in self.reports:
            terminalreporter.write_line(f"  {nodeid} -> {self._relative(path)}")

    def _display_line(self, english: str, chinese: str, path: Path) -> str:
        label = chinese if self.language == "zh" else english
        return f"{label}: {self._relative(path)}"

    def _relative(self, path: Path) -> Path:
        try:
            return path.relative_to(self.root)
        except ValueError:
            return path

    def _render_index(self) -> str:
        title = "RewindPy 测试失败报告" if self.language == "zh" else "RewindPy test failure reports"
        subtitle = (
            f"共监控 {self.tests_observed} 个测试，{self.failed_tests} 个失败，生成 {len(self.reports)} 份报告。"
            if self.language == "zh"
            else f"Observed {self.tests_observed} tests, {self.failed_tests} failed, {len(self.reports)} reports generated."
        )
        open_text = "打开报告" if self.language == "zh" else "Open report"
        items = []
        for nodeid, path in self.reports:
            href = html.escape(path.name, quote=True)
            safe_nodeid = html.escape(nodeid)
            items.append(
                f'<article class="report-card"><div><span class="status">FAILED</span>'
                f'<h2>{safe_nodeid}</h2></div><a href="{href}">{open_text} →</a></article>'
            )
        cards = "\n".join(items)
        return f"""<!doctype html>
<html lang="{'zh-CN' if self.language == 'zh' else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; min-height: 100vh; background: #0a0d14; color: #eef2ff; }}
main {{ width: min(980px, calc(100% - 32px)); margin: 0 auto; padding: 64px 0; }}
.brand {{ color: #8b9cff; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ margin: 12px 0 10px; font-size: clamp(32px, 5vw, 54px); letter-spacing: -.04em; }}
.subtitle {{ margin: 0 0 36px; color: #9aa5bd; font-size: 17px; }}
.report-list {{ display: grid; gap: 14px; }}
.report-card {{ display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 22px 24px; border: 1px solid #252b3b; border-radius: 18px; background: #111622; box-shadow: 0 12px 36px rgba(0,0,0,.22); }}
.report-card:hover {{ border-color: #5664a8; transform: translateY(-1px); }}
.report-card h2 {{ margin: 8px 0 0; font: 600 15px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; overflow-wrap: anywhere; }}
.status {{ display: inline-flex; padding: 4px 8px; border-radius: 999px; background: rgba(255,92,122,.12); color: #ff7692; font-size: 11px; font-weight: 800; letter-spacing: .08em; }}
a {{ flex: 0 0 auto; color: #cad2ff; text-decoration: none; font-weight: 700; }}
@media (max-width: 640px) {{ .report-card {{ align-items: flex-start; flex-direction: column; }} }}
</style>
</head>
<body><main><div class="brand">RewindPy</div><h1>{html.escape(title)}</h1><p class="subtitle">{html.escape(subtitle)}</p><section class="report-list">{cards}</section></main></body>
</html>"""


def _report_filename(nodeid: str) -> str:
    readable = _SAFE_NAME.sub("__", nodeid).strip("._-")
    readable = readable[:120] or "failed-test"
    digest = hashlib.sha1(nodeid.encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
    return f"{readable}__{digest}.html"
