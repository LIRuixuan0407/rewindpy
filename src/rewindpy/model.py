from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TraceEvent:
    step: int
    event: str
    file: str
    line: int
    function: str
    depth: int
    locals: dict[str, Any] = field(default_factory=dict)
    changes: dict[str, dict[str, Any]] = field(default_factory=dict)
    change_line: int | None = None
    return_value: Any = None
    exception_type: str | None = None
    exception_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CrashInfo:
    exception_type: str
    message: str
    file: str | None
    line: int | None
    function: str | None
    traceback: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TraceStats:
    max_events: int
    total_events: int
    retained_events: int
    discarded_events: int
    traced_files: int
    excluded_events: int
    duration_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
