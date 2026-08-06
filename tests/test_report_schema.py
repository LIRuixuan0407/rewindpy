from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from rewindpy.report import HTML_TEMPLATE, write_report
from rewindpy.schema import (
    REPORT_SCHEMA_VERSION,
    ReportSchemaError,
    UnsupportedReportSchemaError,
    prepare_report_payload,
    verify_report_integrity,
)


def _event(step: int = 1) -> dict:
    return {
        "step": step,
        "event": "line",
        "file": "app.py",
        "line": 1,
        "function": "main",
        "depth": 1,
        "locals": {"name": "Alice"},
        "changes": {},
    }


def _payload() -> dict:
    return {
        "language": "en",
        "project_root": "/project",
        "target": "/project/app.py",
        "arguments": [],
        "crash": {
            "exception_type": "RuntimeError",
            "message": "boom",
            "file": "app.py",
            "line": 1,
            "function": "main",
            "traceback": [],
        },
        "analysis": None,
        "crash_slice": {"steps": [1]},
        "events": [_event()],
        "trace_stats": {"retained_events": 1},
        "sources": {"app.py": ["raise RuntimeError('boom')"]},
    }


def test_prepares_schema_v2_and_normalizes_legacy_sources() -> None:
    payload = _payload()
    payload["version"] = 6
    payload["sources"] = {
        "array.py": ["first", "second"],
        "string.py": "first\nsecond",
        "object.py": {"content": "first\nsecond"},
    }

    document = prepare_report_payload(payload, rewindpy_version="0.2.0.dev0")

    assert document["schema_version"] == REPORT_SCHEMA_VERSION
    assert document["rewindpy_version"] == "0.2.0.dev0"
    assert document["legacy_report_version"] == 6
    assert document["sources"]["array.py"]["lines"] == ["first", "second"]
    assert document["sources"]["string.py"]["lines"] == ["first", "second"]
    assert document["sources"]["object.py"]["lines"] == ["first", "second"]
    assert document["integrity"]["status"] == "ok"
    assert document["integrity"]["event_count"] == 1
    assert document["integrity"]["source_count"] == 3
    assert len(document["integrity"]["digest"]) == 64
    verify_report_integrity(document)


def test_integrity_verification_detects_tampering() -> None:
    document = prepare_report_payload(_payload())
    document["events"][0]["locals"]["name"] = "Mallory"

    with pytest.raises(ReportSchemaError, match="digest does not match"):
        verify_report_integrity(document)


def test_preparation_is_idempotent_for_schema_v2() -> None:
    first = prepare_report_payload(_payload())
    second = prepare_report_payload(first)

    assert second["schema_version"] == REPORT_SCHEMA_VERSION
    assert second["sources"] == first["sources"]
    assert second["integrity"] == first["integrity"]


def test_rejects_future_schema_versions() -> None:
    payload = _payload()
    payload["schema_version"] = REPORT_SCHEMA_VERSION + 1

    with pytest.raises(UnsupportedReportSchemaError, match="newer than supported"):
        prepare_report_payload(payload)


def test_rejects_invalid_event_boundaries() -> None:
    payload = _payload()
    payload["events"][0]["step"] = "1"

    with pytest.raises(ReportSchemaError, match=r"events\[0\]\.step"):
        prepare_report_payload(payload)


def test_write_report_embeds_schema_metadata(tmp_path: Path) -> None:
    output = tmp_path / "report.html"

    write_report(output, _payload())

    html = output.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="rewind-data" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    document = json.loads(match.group(1))
    assert document["schema_version"] == REPORT_SCHEMA_VERSION
    assert document["rewindpy_version"]
    assert document["sources"]["app.py"]["lines"] == ["raise RuntimeError('boom')"]
    assert document["integrity"]["event_count"] == 1
    verify_report_integrity(document)


def test_frontend_has_schema_compatibility_and_friendly_error_page() -> None:
    for marker in (
        "CURRENT_REPORT_SCHEMA=2",
        "function normalizePayload",
        "function showReportError",
        "unsupported report schema",
        "此报告需要更新版本的 RewindPy",
    ):
        assert marker in HTML_TEMPLATE
