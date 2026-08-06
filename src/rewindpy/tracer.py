from __future__ import annotations

import linecache
import os
import sys
import traceback as traceback_module
from collections import deque
from pathlib import Path
from types import FrameType, TracebackType
from typing import Any, Callable

from .model import CrashInfo, TraceEvent
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
    ) -> None:
        self.project_root = project_root.resolve()
        self.max_events = max_events
        self.serializer = serializer or SafeSerializer()
        self.events: deque[TraceEvent] = deque(maxlen=max_events)
        self._step = 0
        self._previous_locals: dict[int, dict[str, Any]] = {}
        self._enabled = False

    def start(self) -> None:
        self._enabled = True
        sys.settrace(self._trace)

    def stop(self) -> None:
        sys.settrace(None)
        self._enabled = False

    def _is_project_file(self, filename: str) -> bool:
        if not filename or filename.startswith("<"):
            return False
        try:
            path = Path(filename).resolve()
            path.relative_to(self.project_root)
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
        locals_snapshot = self.serializer.serialize_locals(frame.f_locals)
        frame_key = id(frame)
        previous = self._previous_locals.get(frame_key, {})
        changes = self._diff(previous, locals_snapshot)
        self._previous_locals[frame_key] = locals_snapshot

        exception_type: str | None = None
        exception_message: str | None = None
        if event == "exception" and isinstance(arg, tuple) and len(arg) == 3:
            exc_type, exc_value, _ = arg
            exception_type = getattr(exc_type, "__name__", str(exc_type))
            exception_message = str(exc_value)

        file_path = str(Path(frame.f_code.co_filename).resolve().relative_to(self.project_root))
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
                exception_type=exception_type,
                exception_message=exception_message,
            )
        )

        if event == "return":
            self._previous_locals.pop(frame_key, None)

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
