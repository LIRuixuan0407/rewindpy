from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Sequence

from .analysis import analyze_crash, build_crash_slice
from .optimize import compress_repeated_cycles, fit_report_budget
from .report import write_report
from .tracer import RewindTracer, build_crash_info


def run_target(
    target: Path,
    target_args: Sequence[str],
    *,
    output: Path,
    max_events: int = 5_000,
    language: str = "en",
    include_paths: Sequence[Path] = (),
    exclude_paths: Sequence[Path] = (),
    max_report_mb: float = 20.0,
) -> int:
    target = target.resolve()
    if not target.is_file():
        raise FileNotFoundError(f"Target script not found: {target}")

    project_root = target.parent
    resolved_includes = [path if path.is_absolute() else project_root / path for path in include_paths]
    resolved_excludes = [path if path.is_absolute() else project_root / path for path in exclude_paths]
    tracer = RewindTracer(
        project_root,
        max_events=max_events,
        include_paths=resolved_includes,
        exclude_paths=resolved_excludes,
    )
    old_argv = sys.argv[:]
    old_path = sys.path[:]
    sys.argv = [str(target), *target_args]
    sys.path.insert(0, str(project_root))

    try:
        tracer.start()
        runpy.run_path(str(target), run_name="__main__")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if code == 0:
            return 0
        tracer.stop()
        crash = build_crash_info(type(exc), exc, exc.__traceback__, project_root)
        _write(output, tracer, crash.to_dict(), target, target_args, language, max_report_mb)
        return int(code)
    except BaseException as exc:
        tracer.stop()
        crash = build_crash_info(type(exc), exc, exc.__traceback__, project_root)
        _write(output, tracer, crash.to_dict(), target, target_args, language, max_report_mb)
        return 1
    finally:
        tracer.stop()
        sys.argv = old_argv
        sys.path[:] = old_path

    return 0


def _write(
    output: Path,
    tracer: RewindTracer,
    crash: dict,
    target: Path,
    target_args: Sequence[str],
    language: str,
    max_report_mb: float,
) -> None:
    events = tracer.event_dicts()
    analysis = analyze_crash(events, crash, language=language)
    crash_slice = build_crash_slice(events, crash, analysis)
    report_events, compressed_events = compress_repeated_cycles(events)
    stats = tracer.stats().to_dict()
    stats["report_events"] = len(report_events)
    stats["compressed_events"] = compressed_events
    payload = {
        "version": 6,
        "language": language,
        "target": str(target),
        "arguments": list(target_args),
        "crash": crash,
        "analysis": analysis,
        "crash_slice": crash_slice,
        "events": report_events,
        "trace_stats": stats,
        "sources": tracer.source_files(),
    }
    protected_steps = set(crash_slice.get("steps") or [])
    if analysis and analysis.get("origin_step") is not None:
        protected_steps.add(int(analysis["origin_step"]))
    payload, trimmed = fit_report_budget(
        payload,
        max_bytes=max(1, int(max_report_mb * 1024 * 1024)),
        protected_steps=protected_steps,
    )
    stats = payload["trace_stats"]
    stats["report_trimmed_events"] = trimmed
    stats["report_events"] = len(payload["events"])
    stats["report_size_bytes"] = len(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    )
    write_report(output, payload)
