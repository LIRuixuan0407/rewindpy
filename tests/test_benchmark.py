from __future__ import annotations

from benchmarks.report_benchmark import make_payload, run_benchmark


def test_benchmark_payload_matches_requested_scale() -> None:
    payload = make_payload(37, source_count=3)

    assert len(payload["events"]) == 37
    assert len(payload["sources"]) == 3
    assert payload["events"][-1]["step"] == 37


def test_report_benchmark_smoke() -> None:
    result = run_benchmark(event_count=120, source_count=2, iterations=1)

    assert result.events == 120
    assert result.files == 2
    assert result.html_bytes > 1_000
    assert result.median_seconds > 0
    assert result.events_per_second > 0
