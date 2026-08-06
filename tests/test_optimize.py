from rewindpy.optimize import compress_repeated_cycles, fit_report_budget


def quiet(step: int, line: int) -> dict:
    return {
        "step": step,
        "event": "line",
        "file": "loop.py",
        "line": line,
        "function": "work",
        "depth": 2,
        "locals": {"index": step},
        "changes": {},
        "exception_type": None,
    }


def test_compresses_repeated_two_line_loop_cycles():
    events = []
    step = 1
    for _ in range(20):
        events.extend([quiet(step, 4), quiet(step + 1, 5)])
        step += 2

    compressed, removed = compress_repeated_cycles(events)

    assert len(compressed) == 1
    assert removed == 39
    assert compressed[0]["event"] == "repeat"
    assert compressed[0]["repeat_count"] == 20
    assert compressed[0]["pattern_size"] == 2
    assert compressed[0]["step"] == 1
    assert compressed[0]["step_end"] == 40


def test_does_not_compress_exception_or_non_line_events():
    events = [quiet(1, 4), quiet(2, 4), quiet(3, 4)]
    events[1]["event"] = "call"
    events[2]["exception_type"] = "RuntimeError"

    compressed, removed = compress_repeated_cycles(events)

    assert compressed == events
    assert removed == 0


def test_report_budget_preserves_protected_and_exception_events():
    events = [quiet(step, step) for step in range(1, 80)]
    events[-1]["event"] = "exception"
    events[-1]["exception_type"] = "RuntimeError"
    payload = {
        "events": events,
        "crash_slice": {"steps": [20, 79]},
        "trace_stats": {},
        "sources": {},
    }

    fitted, removed = fit_report_budget(payload, max_bytes=2_500, protected_steps={20, 79})

    assert removed > 0
    retained_steps = {event["step"] for event in fitted["events"]}
    assert 20 in retained_steps
    assert 79 in retained_steps
    assert any(event.get("exception_type") == "RuntimeError" for event in fitted["events"])
