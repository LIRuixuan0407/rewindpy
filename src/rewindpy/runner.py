from __future__ import annotations

import runpy
import sys
from pathlib import Path
from typing import Sequence

from .report import write_report
from .tracer import RewindTracer, build_crash_info


def run_target(
    target: Path,
    target_args: Sequence[str],
    *,
    output: Path,
    max_events: int = 5_000,
) -> int:
    target = target.resolve()
    if not target.is_file():
        raise FileNotFoundError(f"Target script not found: {target}")

    project_root = target.parent
    tracer = RewindTracer(project_root, max_events=max_events)
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
        _write(output, tracer, crash.to_dict(), target, target_args)
        return int(code)
    except BaseException as exc:
        tracer.stop()
        crash = build_crash_info(type(exc), exc, exc.__traceback__, project_root)
        _write(output, tracer, crash.to_dict(), target, target_args)
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
) -> None:
    payload = {
        "version": 1,
        "target": str(target),
        "arguments": list(target_args),
        "crash": crash,
        "events": tracer.event_dicts(),
        "sources": tracer.source_files(),
    }
    write_report(output, payload)
