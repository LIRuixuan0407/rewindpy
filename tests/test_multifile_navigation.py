from __future__ import annotations

import json
import re
from pathlib import Path

from rewindpy.demos import create_demo_report, demo_names
from rewindpy.report import _REPORT_MESSAGES, HTML_TEMPLATE


def _embedded_payload(report: Path) -> dict:
    html = report.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="rewind-data" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return json.loads(match.group(1))


def test_report_has_multi_file_workspace_and_search() -> None:
    for marker in (
        'id="fileExplorer"',
        'id="fileTree"',
        'id="quickOpen"',
        'id="quickOpenInput"',
        'id="sourceSearch"',
        'id="sourceSearchInput"',
        'id="globalSearch"',
        'id="globalSearchInput"',
        "function buildFileTree",
        "function openFile",
        "function jumpToLocation",
        "function showQuickOpen",
        "function showSourceSearch",
        "function showGlobalSearch",
        "function collectGlobalResults",
    ):
        assert marker in HTML_TEMPLATE


def test_report_has_file_and_search_shortcuts() -> None:
    assert "key==='p'" in HTML_TEMPLATE
    assert "event.shiftKey&&key==='f'" in HTML_TEMPLATE
    assert "key==='f'" in HTML_TEMPLATE
    assert "replaceAll('\\\\','/')" in HTML_TEMPLATE


def test_multi_file_messages_are_bilingual() -> None:
    assert _REPORT_MESSAGES["en"]["file_explorer"] == "Files"
    assert _REPORT_MESSAGES["zh"]["file_explorer"] == "文件"
    assert "current file" in _REPORT_MESSAGES["en"]["source_search_placeholder"]
    assert "当前文件" in _REPORT_MESSAGES["zh"]["source_search_placeholder"]


def test_multi_file_demo_captures_cross_file_execution(tmp_path: Path) -> None:
    report = tmp_path / "multi-file.html"

    create_demo_report("multi-file", output=report, language="en")

    payload = _embedded_payload(report)
    assert {"app.py", "service.py", "config_loader.py"} <= set(payload["sources"])
    assert {event["file"] for event in payload["events"]} >= {
        "app.py",
        "service.py",
        "config_loader.py",
    }
    chain_files = {item["file"] for item in payload["exception_chain"]["items"]}
    assert {"service.py", "config_loader.py"} <= chain_files


def test_multi_file_demo_is_available_from_cli_choices() -> None:
    assert "multi-file" in demo_names()
