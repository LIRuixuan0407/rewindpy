from __future__ import annotations

import json
import re
from pathlib import Path

from rewindpy.runner import run_target
from rewindpy.tracer import attach_exception_steps, build_exception_chain


def _explicit_chain() -> RuntimeError:
    try:
        json.loads('{"port": 8000,}')
    except json.JSONDecodeError as inner:
        if hasattr(inner, "add_note"):
            inner.add_note("malformed demo configuration")
        try:
            raise ValueError("configuration is invalid") from inner
        except ValueError as middle:
            try:
                raise RuntimeError("application startup failed") from middle
            except RuntimeError as outer:
                return outer
    raise AssertionError("chain was not created")


def _implicit_context() -> RuntimeError:
    try:
        1 / 0
    except ZeroDivisionError:
        try:
            raise RuntimeError("wrapper failed")
        except RuntimeError as outer:
            return outer
    raise AssertionError("context was not created")


def _suppressed_context() -> RuntimeError:
    try:
        1 / 0
    except ZeroDivisionError:
        try:
            raise RuntimeError("clean public error") from None
        except RuntimeError as outer:
            return outer
    raise AssertionError("suppressed context was not created")


def test_builds_explicit_cause_chain_outermost_first(tmp_path: Path) -> None:
    chain = build_exception_chain(_explicit_chain(), tmp_path)

    assert [item["exception_type"] for item in chain["items"]] == [
        "RuntimeError",
        "ValueError",
        "JSONDecodeError",
    ]
    assert [item["relation_to_next"] for item in chain["items"]] == [
        "cause",
        "cause",
        None,
    ]
    assert chain["truncated"] is False
    assert chain["cycle_detected"] is False
    if hasattr(BaseException(), "add_note"):
        assert chain["items"][-1]["notes"] == ["malformed demo configuration"]


def test_builds_implicit_context_and_respects_suppression(tmp_path: Path) -> None:
    context_chain = build_exception_chain(_implicit_context(), tmp_path)
    suppressed_chain = build_exception_chain(_suppressed_context(), tmp_path)

    assert [item["exception_type"] for item in context_chain["items"]] == [
        "RuntimeError",
        "ZeroDivisionError",
    ]
    assert context_chain["items"][0]["relation_to_next"] == "context"
    assert [item["exception_type"] for item in suppressed_chain["items"]] == [
        "RuntimeError"
    ]
    assert suppressed_chain["items"][0]["suppress_context"] is True


def test_exception_chain_has_cycle_and_depth_guards(tmp_path: Path) -> None:
    first = RuntimeError("first")
    second = ValueError("second")
    first.__cause__ = second
    second.__cause__ = first

    cycle = build_exception_chain(first, tmp_path)
    assert cycle["cycle_detected"] is True
    assert cycle["truncated"] is False
    assert len(cycle["items"]) == 2

    root: BaseException = RuntimeError("0")
    current = root
    for value in range(1, 8):
        next_exception = RuntimeError(str(value))
        current.__cause__ = next_exception
        current = next_exception

    truncated = build_exception_chain(root, tmp_path, max_depth=3)
    assert truncated["truncated"] is True
    assert truncated["cycle_detected"] is False
    assert len(truncated["items"]) == 3


def test_attaches_matching_exception_events() -> None:
    chain = {
        "items": [
            {
                "exception_type": "RuntimeError",
                "message": "outer",
                "file": "app.py",
                "line": 8,
                "function": "main",
                "event_step": None,
            },
            {
                "exception_type": "ValueError",
                "message": "inner",
                "file": "app.py",
                "line": 3,
                "function": "parse",
                "event_step": None,
            },
        ]
    }
    events = [
        {
            "step": 4,
            "event": "exception",
            "exception_type": "ValueError",
            "exception_message": "inner",
            "file": "app.py",
            "line": 3,
            "function": "parse",
        },
        {
            "step": 9,
            "event": "exception",
            "exception_type": "RuntimeError",
            "exception_message": "outer",
            "file": "app.py",
            "line": 8,
            "function": "main",
        },
    ]

    attached = attach_exception_steps(chain, events)

    assert [item["event_step"] for item in attached["items"]] == [9, 4]


def test_runner_embeds_exception_chain_and_timeline_steps(tmp_path: Path) -> None:
    target = tmp_path / "app.py"
    output = tmp_path / "report.html"
    target.write_text(
        "class AppError(RuntimeError):\n"
        "    pass\n\n"
        "def parse():\n"
        "    try:\n"
        "        int('not-a-number')\n"
        "    except ValueError as exc:\n"
        "        raise AppError('parse failed') from exc\n\n"
        "parse()\n",
        encoding="utf-8",
    )

    assert run_target(target, [], output=output) == 1
    html = output.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="rewind-data" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    payload = json.loads(match.group(1))
    items = payload["exception_chain"]["items"]

    assert [item["exception_type"] for item in items] == ["AppError", "ValueError"]
    assert items[0]["relation_to_next"] == "cause"
    assert all(isinstance(item["event_step"], int) for item in items)
    assert {item["event_step"] for item in items}.issubset(
        set(payload["crash_slice"]["steps"])
    )
    assert 'id="exceptionsTab"' in html
    assert "function renderExceptions" in html
