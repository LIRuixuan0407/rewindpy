from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rewindpy.report import write_report


@dataclass(frozen=True)
class BenchmarkResult:
    events: int
    files: int
    iterations: int
    median_seconds: float
    min_seconds: float
    max_seconds: float
    html_bytes: int
    html_megabytes: float
    events_per_second: float


def make_payload(event_count: int, *, source_count: int = 4) -> dict[str, Any]:
    if event_count < 1:
        raise ValueError("event_count must be positive")
    if source_count < 1:
        raise ValueError("source_count must be positive")

    sources: dict[str, list[str]] = {}
    for file_index in range(source_count):
        file_name = f"package/module_{file_index}.py"
        sources[file_name] = [
            f"def function_{line_index}(value): return value + {line_index}"
            for line_index in range(1, 251)
        ]

    events: list[dict[str, Any]] = []
    for index in range(event_count):
        file_index = index % source_count
        file_name = f"package/module_{file_index}.py"
        line = (index % 250) + 1
        events.append(
            {
                "step": index + 1,
                "event": "line",
                "file": file_name,
                "line": line,
                "function": f"function_{line}",
                "depth": 1 + (index % 8),
                "locals": {
                    "index": index,
                    "file_index": file_index,
                    "label": f"event-{index}",
                },
                "changes": {
                    "index": {
                        "before": index - 1 if index else None,
                        "after": index,
                    }
                },
            }
        )

    crash_file = f"package/module_{(event_count - 1) % source_count}.py"
    crash_line = ((event_count - 1) % 250) + 1
    return {
        "language": "en",
        "project_root": "/benchmark",
        "target": "/benchmark/package/module_0.py",
        "arguments": [],
        "crash": {
            "exception_type": "RuntimeError",
            "message": "benchmark crash",
            "file": crash_file,
            "line": crash_line,
            "function": f"function_{crash_line}",
            "traceback": [],
        },
        "exception_chain": {"items": []},
        "analysis": None,
        "crash_slice": {
            "steps": list(range(max(1, event_count - 99), event_count + 1))
        },
        "events": events,
        "trace_stats": {
            "max_events": event_count,
            "total_events": event_count,
            "retained_events": event_count,
            "discarded_events": 0,
            "traced_files": source_count,
            "excluded_events": 0,
            "duration_seconds": 0.0,
            "report_events": event_count,
            "compressed_events": 0,
            "report_trimmed_events": 0,
            "report_size_bytes": 0,
        },
        "sources": sources,
    }


def run_benchmark(
    *,
    event_count: int = 5_000,
    source_count: int = 4,
    iterations: int = 3,
) -> BenchmarkResult:
    if iterations < 1:
        raise ValueError("iterations must be positive")

    payload = make_payload(event_count, source_count=source_count)
    timings: list[float] = []
    html_bytes = 0
    with tempfile.TemporaryDirectory(prefix="rewindpy-benchmark-") as temp_dir:
        output = Path(temp_dir) / "report.html"
        for _ in range(iterations):
            started = time.perf_counter()
            write_report(output, payload)
            timings.append(time.perf_counter() - started)
            html_bytes = output.stat().st_size

    median_seconds = statistics.median(timings)
    return BenchmarkResult(
        events=event_count,
        files=source_count,
        iterations=iterations,
        median_seconds=median_seconds,
        min_seconds=min(timings),
        max_seconds=max(timings),
        html_bytes=html_bytes,
        html_megabytes=html_bytes / (1024 * 1024),
        events_per_second=event_count / median_seconds,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark RewindPy report generation.")
    parser.add_argument("--events", type=int, default=5_000)
    parser.add_argument("--files", type=int, default=4)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--max-seconds", type=float)
    parser.add_argument("--max-html-mb", type=float)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_benchmark(
        event_count=args.events,
        source_count=args.files,
        iterations=args.iterations,
    )
    if args.json_output:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(
            f"events={result.events} files={result.files} "
            f"median={result.median_seconds:.3f}s "
            f"throughput={result.events_per_second:,.0f} events/s "
            f"html={result.html_megabytes:.2f} MiB"
        )

    failed = False
    if args.max_seconds is not None and result.median_seconds > args.max_seconds:
        print(
            f"benchmark exceeded --max-seconds: "
            f"{result.median_seconds:.3f} > {args.max_seconds:.3f}"
        )
        failed = True
    if args.max_html_mb is not None and result.html_megabytes > args.max_html_mb:
        print(
            f"benchmark exceeded --max-html-mb: "
            f"{result.html_megabytes:.2f} > {args.max_html_mb:.2f}"
        )
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
