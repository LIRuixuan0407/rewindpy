from __future__ import annotations

import hashlib
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

    def pytest_terminal_summary(
        self,
        terminalreporter: pytest.TerminalReporter,
        exitstatus: int,
        config: pytest.Config,
    ) -> None:
        del exitstatus, config
        if not self.reports:
            return
        terminalreporter.section("RewindPy reports / RewindPy 报告", sep="=")
        for nodeid, path in self.reports:
            try:
                display = path.relative_to(self.root)
            except ValueError:
                display = path
            terminalreporter.write_line(f"{nodeid} -> {display}")


def _report_filename(nodeid: str) -> str:
    readable = _SAFE_NAME.sub("__", nodeid).strip("._-")
    readable = readable[:120] or "failed-test"
    digest = hashlib.sha1(nodeid.encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
    return f"{readable}__{digest}.html"
