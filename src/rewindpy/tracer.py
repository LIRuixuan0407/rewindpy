from __future__ import annotations

import linecache
import sys
import time
import traceback as traceback_module
from collections import deque
from collections.abc import Callable
from pathlib import Path
from types import FrameType, TracebackType
from typing import Any

from .model import CrashInfo, TraceEvent, TraceStats
from .serialize import SafeSerializer

TraceFunction = Callable[[FrameType, str, Any], Any]


class RewindTracer:
    """Capture a bounded, project-local history of Python execution events."""

    def __init__(
        self,
        project_root: Path,
        *,
        max_events: int = 5_000,
        serializer: SafeSerializer | None = None,
        include_paths: list[Path] | None = None,
        exclude_paths: list[Path] | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.max_events = max_events
        self.serializer = serializer or SafeSerializer()
        self.include_paths = [path.resolve() for path in (include_paths or [])]
        defaults = [".venv", "venv", "site-packages", "__pycache__", ".git", "build", "dist"]
        self.exclude_paths = [self.project_root / item for item in defaults]
        self.exclude_paths.extend(path.resolve() for path in (exclude_paths or []))
        self.events: deque[TraceEvent] = deque(maxlen=max_events)
        self._step = 0
        self._previous_locals: dict[int, dict[str, Any]] = {}
        self._previous_lines: dict[int, int] = {}
        self._enabled = False
        self._total_events = 0
        self._excluded_events = 0
        self._traced_files: set[str] = set()
        self._started_at = 0.0
        self._duration_seconds = 0.0

    def start(self) -> None:
        self._started_at = time.perf_counter()
        self._enabled = True
        sys.settrace(self._trace)

    def stop(self) -> None:
        sys.settrace(None)
        if self._enabled and self._started_at:
            self._duration_seconds += time.perf_counter() - self._started_at
            self._started_at = 0.0
        self._enabled = False

    def _is_project_file(self, filename: str) -> bool:
        if not filename or filename.startswith("<"):
            return False
        try:
            path = Path(filename).resolve()
            path.relative_to(self.project_root)
            if self.include_paths and not any(_is_relative_to(path, root) for root in self.include_paths):
                self._excluded_events += 1
                return False
            if any(_is_relative_to(path, root) for root in self.exclude_paths):
                self._excluded_events += 1
                return False
            return True
        except (OSError, ValueError):
            return False

    def _trace(self, frame: FrameType, event: str, arg: Any) -> TraceFunction | None:
        filename = frame.f_code.co_filename
        if not self._is_project_file(filename):
            return None

        if event not in {"call", "line", "return", "exception"}:
            return self._trace

        try:
            self._record(frame, event, arg)
        except Exception:
            # A debugger must not become the reason the target program fails.
            return self._trace
        return self._trace

    def _record(self, frame: FrameType, event: str, arg: Any) -> None:
        self._step += 1
        self._total_events += 1
        locals_snapshot = self.serializer.serialize_locals(frame.f_locals)
        frame_key = id(frame)
        previous = self._previous_locals.get(frame_key, {})
        changes = self._diff(previous, locals_snapshot)
        change_line = self._previous_lines.get(frame_key)
        self._previous_locals[frame_key] = locals_snapshot

        if event == "line":
            self._previous_lines[frame_key] = frame.f_lineno

        return_value: Any = None
        if event == "return":
            return_value = self.serializer.serialize(arg)

        exception_type: str | None = None
        exception_message: str | None = None
        if event == "exception" and isinstance(arg, tuple) and len(arg) == 3:
            exc_type, exc_value, _ = arg
            exception_type = getattr(exc_type, "__name__", str(exc_type))
            exception_message = str(exc_value)

        file_path = str(Path(frame.f_code.co_filename).resolve().relative_to(self.project_root))
        self._traced_files.add(file_path)
        self.events.append(
            TraceEvent(
                step=self._step,
                event=event,
                file=file_path,
                line=frame.f_lineno,
                function=frame.f_code.co_name,
                depth=self._stack_depth(frame),
                locals=locals_snapshot,
                changes=changes,
                change_line=change_line,
                return_value=return_value,
                exception_type=exception_type,
                exception_message=exception_message,
            )
        )

        if event == "return":
            self._previous_locals.pop(frame_key, None)
            self._previous_lines.pop(frame_key, None)

    @staticmethod
    def _stack_depth(frame: FrameType) -> int:
        depth = 0
        current: FrameType | None = frame
        while current is not None:
            depth += 1
            current = current.f_back
        return depth

    @staticmethod
    def _diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        missing = "<not set>"
        for key in sorted(before.keys() | after.keys()):
            old = before.get(key, missing)
            new = after.get(key, missing)
            if old != new:
                result[key] = {"before": old, "after": new}
        return result


    def stats(self) -> TraceStats:
        retained = len(self.events)
        return TraceStats(
            max_events=self.max_events,
            total_events=self._total_events,
            retained_events=retained,
            discarded_events=max(0, self._total_events - retained),
            traced_files=len(self._traced_files),
            excluded_events=self._excluded_events,
            duration_seconds=round(self._duration_seconds, 6),
        )

    def event_dicts(self) -> list[dict[str, Any]]:
        return [event.to_dict() for event in self.events]

    def source_files(self) -> dict[str, list[str]]:
        files = sorted({event.file for event in self.events})
        result: dict[str, list[str]] = {}
        for relative in files:
            absolute = self.project_root / relative
            try:
                result[relative] = [
                    self.serializer.redact_source_line(line)
                    for line in absolute.read_text(encoding="utf-8").splitlines()
                ]
            except (OSError, UnicodeDecodeError):
                result[relative] = []
        return result


def build_crash_info(
    exc_type: type[BaseException],
    exc_value: BaseException,
    tb: TracebackType | None,
    project_root: Path,
) -> CrashInfo:
    frames: list[dict[str, Any]] = []
    last_project_frame: dict[str, Any] | None = None
    root = project_root.resolve()

    for frame_summary in traceback_module.extract_tb(tb):
        filename = Path(frame_summary.filename).resolve()
        try:
            relative = str(filename.relative_to(root))
            is_project = True
        except ValueError:
            relative = str(filename)
            is_project = False

        frame_data = {
            "file": relative,
            "line": frame_summary.lineno,
            "function": frame_summary.name,
            "source": frame_summary.line or linecache.getline(str(filename), frame_summary.lineno).strip(),
            "project_file": is_project,
        }
        frames.append(frame_data)
        if is_project:
            last_project_frame = frame_data

    return CrashInfo(
        exception_type=exc_type.__name__,
        message=str(exc_value),
        file=last_project_frame["file"] if last_project_frame else None,
        line=last_project_frame["line"] if last_project_frame else None,
        function=last_project_frame["function"] if last_project_frame else None,
        traceback=frames,
    )


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
