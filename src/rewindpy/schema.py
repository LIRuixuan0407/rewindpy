from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from . import __version__

REPORT_SCHEMA_VERSION = 2
MIN_REPORT_SCHEMA_VERSION = 1


class ReportSchemaError(ValueError):
    """Raised when report data cannot be normalized into a supported schema."""

    def __init__(self, message: str, *, path: str = "$") -> None:
        self.path = path
        super().__init__(f"{path}: {message}")


class UnsupportedReportSchemaError(ReportSchemaError):
    """Raised when report data requires a newer RewindPy report viewer."""


def prepare_report_payload(
    payload: Mapping[str, Any],
    *,
    rewindpy_version: str = __version__,
) -> dict[str, Any]:
    """Normalize and validate report data before embedding it in HTML.

    Schema v1 represents reports generated before explicit schema metadata was
    introduced. Common v1 source shapes (strings, line arrays, and source
    objects) are accepted and converted into the canonical v2 representation.
    """
    if not isinstance(payload, Mapping):
        raise ReportSchemaError("report payload must be an object")

    source = deepcopy(dict(payload))
    schema_version = _read_schema_version(source.get("schema_version"))
    if schema_version > REPORT_SCHEMA_VERSION:
        raise UnsupportedReportSchemaError(
            f"schema version {schema_version} is newer than supported version "
            f"{REPORT_SCHEMA_VERSION}",
            path="$.schema_version",
        )

    document = dict(source)
    legacy_version = document.pop("version", None)
    if legacy_version is not None and "legacy_report_version" not in document:
        document["legacy_report_version"] = legacy_version

    document["schema_version"] = REPORT_SCHEMA_VERSION
    document["rewindpy_version"] = str(
        source.get("rewindpy_version") or rewindpy_version
    )
    document["language"] = "zh" if source.get("language") == "zh" else "en"
    document["project_root"] = _string(source.get("project_root"))
    document["target"] = _string(source.get("target"))
    document["arguments"] = _string_list(source.get("arguments"), "$.arguments")
    document["crash"] = _normalize_crash(source.get("crash"))
    document["exception_chain"] = _normalize_exception_chain(
        source.get("exception_chain"),
        document["crash"],
    )
    document["analysis"] = _optional_object(source.get("analysis"), "$.analysis")
    document["crash_slice"] = _normalize_crash_slice(source.get("crash_slice"))
    document["events"] = _normalize_events(source.get("events"))
    document["trace_stats"] = _normalize_trace_stats(source.get("trace_stats"))
    document["sources"] = _normalize_sources(source.get("sources"))

    document.pop("integrity", None)
    validate_report_payload(document)
    document["integrity"] = _build_integrity(document)
    return document


def verify_report_integrity(payload: Mapping[str, Any]) -> None:
    """Verify the structural metadata and SHA-256 digest of a v2 report."""
    validate_report_payload(payload)
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ReportSchemaError("must be an object", path="$.integrity")

    expected = _build_integrity(payload)
    if integrity.get("status") != "ok":
        raise ReportSchemaError("status must be 'ok'", path="$.integrity.status")
    if integrity.get("algorithm") != "sha256":
        raise ReportSchemaError(
            "algorithm must be 'sha256'",
            path="$.integrity.algorithm",
        )
    digest = integrity.get("digest")
    if not isinstance(digest, str) or not hmac.compare_digest(digest, expected["digest"]):
        raise ReportSchemaError(
            "digest does not match report contents",
            path="$.integrity.digest",
        )
    for field in ("event_count", "source_count", "source_line_count"):
        if integrity.get(field) != expected[field]:
            raise ReportSchemaError(
                f"does not match computed {field}",
                path=f"$.integrity.{field}",
            )


def validate_report_payload(payload: Mapping[str, Any]) -> None:
    """Validate the canonical v2 representation.

    This function intentionally checks the boundary between Python and the
    embedded report viewer. It prevents malformed data from becoming a blank or
    partially broken report.
    """
    if payload.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise ReportSchemaError(
            f"expected schema version {REPORT_SCHEMA_VERSION}",
            path="$.schema_version",
        )
    if not isinstance(payload.get("rewindpy_version"), str) or not payload.get(
        "rewindpy_version"
    ):
        raise ReportSchemaError("must be a non-empty string", path="$.rewindpy_version")
    if not isinstance(payload.get("events"), list):
        raise ReportSchemaError("must be an array", path="$.events")
    if not isinstance(payload.get("sources"), dict):
        raise ReportSchemaError("must be an object", path="$.sources")
    if not isinstance(payload.get("crash"), dict):
        raise ReportSchemaError("must be an object", path="$.crash")
    if not isinstance(payload.get("trace_stats"), dict):
        raise ReportSchemaError("must be an object", path="$.trace_stats")
    _validate_exception_chain(payload.get("exception_chain"))

    for index, event in enumerate(payload["events"]):
        if not isinstance(event, dict):
            raise ReportSchemaError("must be an object", path=f"$.events[{index}]")
        for field in ("step", "line", "depth"):
            if not isinstance(event.get(field), int) or isinstance(event.get(field), bool):
                raise ReportSchemaError(
                    "must be an integer",
                    path=f"$.events[{index}].{field}",
                )
        for field in ("event", "file", "function"):
            if not isinstance(event.get(field), str):
                raise ReportSchemaError(
                    "must be a string",
                    path=f"$.events[{index}].{field}",
                )
        for field in ("locals", "changes"):
            if not isinstance(event.get(field), dict):
                raise ReportSchemaError(
                    "must be an object",
                    path=f"$.events[{index}].{field}",
                )

    for file_name, source in payload["sources"].items():
        if not isinstance(file_name, str):
            raise ReportSchemaError("source paths must be strings", path="$.sources")
        if not isinstance(source, dict):
            raise ReportSchemaError("must be an object", path=f"$.sources[{file_name!r}]")
        lines = source.get("lines")
        if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
            raise ReportSchemaError(
                "lines must be an array of strings",
                path=f"$.sources[{file_name!r}].lines",
            )


def _read_schema_version(value: Any) -> int:
    if value is None:
        return MIN_REPORT_SCHEMA_VERSION
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReportSchemaError("must be an integer", path="$.schema_version")
    if value < MIN_REPORT_SCHEMA_VERSION:
        raise ReportSchemaError(
            f"must be at least {MIN_REPORT_SCHEMA_VERSION}",
            path="$.schema_version",
        )
    return value


def _normalize_crash(value: Any) -> dict[str, Any]:
    crash = _object_or_empty(value, "$.crash")
    traceback_value = crash.get("traceback")
    if traceback_value is None:
        traceback_frames: list[dict[str, Any]] = []
    elif isinstance(traceback_value, Sequence) and not isinstance(
        traceback_value, (str, bytes, bytearray)
    ):
        traceback_frames = []
        for index, frame in enumerate(traceback_value):
            if not isinstance(frame, Mapping):
                raise ReportSchemaError(
                    "must be an object",
                    path=f"$.crash.traceback[{index}]",
                )
            traceback_frames.append(dict(frame))
    else:
        raise ReportSchemaError("must be an array", path="$.crash.traceback")

    return {
        **crash,
        "exception_type": _string(crash.get("exception_type"), "Exception"),
        "message": _string(crash.get("message")),
        "file": _optional_string(crash.get("file")),
        "line": _optional_int(crash.get("line"), "$.crash.line"),
        "function": _optional_string(crash.get("function")),
        "traceback": traceback_frames,
    }


def _normalize_exception_chain(
    value: Any,
    crash: Mapping[str, Any],
) -> dict[str, Any]:
    if value is None:
        raw_chain: Mapping[str, Any] = {}
    elif isinstance(value, Mapping):
        raw_chain = value
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        raw_chain = {"items": value}
    else:
        raise ReportSchemaError("must be an object", path="$.exception_chain")

    raw_items = raw_chain.get("items")
    if raw_items is None:
        raw_items = []
    if not isinstance(raw_items, Sequence) or isinstance(
        raw_items,
        (str, bytes, bytearray),
    ):
        raise ReportSchemaError("must be an array", path="$.exception_chain.items")

    items: list[dict[str, Any]] = []
    for index, raw_item in enumerate(raw_items):
        path = f"$.exception_chain.items[{index}]"
        if not isinstance(raw_item, Mapping):
            raise ReportSchemaError("must be an object", path=path)
        item = dict(raw_item)
        relation = item.get("relation_to_next")
        if relation not in {None, "cause", "context"}:
            raise ReportSchemaError(
                "must be 'cause', 'context', or null",
                path=f"{path}.relation_to_next",
            )
        raw_traceback = item.get("traceback")
        if raw_traceback is None:
            traceback_frames: list[dict[str, Any]] = []
        elif isinstance(raw_traceback, Sequence) and not isinstance(
            raw_traceback,
            (str, bytes, bytearray),
        ):
            traceback_frames = []
            for frame_index, frame in enumerate(raw_traceback):
                if not isinstance(frame, Mapping):
                    raise ReportSchemaError(
                        "must be an object",
                        path=f"{path}.traceback[{frame_index}]",
                    )
                traceback_frames.append(dict(frame))
        else:
            raise ReportSchemaError("must be an array", path=f"{path}.traceback")

        items.append(
            {
                **item,
                "index": index,
                "exception_type": _string(
                    item.get("exception_type"),
                    "Exception",
                ),
                "exception_module": _string(
                    item.get("exception_module"),
                    "builtins",
                ),
                "message": _string(item.get("message")),
                "relation_to_next": relation,
                "suppress_context": bool(item.get("suppress_context", False)),
                "file": _optional_string(item.get("file")),
                "line": _optional_int(item.get("line"), f"{path}.line"),
                "function": _optional_string(item.get("function")),
                "traceback": traceback_frames,
                "notes": _string_list(item.get("notes"), f"{path}.notes"),
                "event_step": _optional_int(
                    item.get("event_step"),
                    f"{path}.event_step",
                ),
            }
        )

    if not items:
        items.append(
            {
                "index": 0,
                "exception_type": _string(
                    crash.get("exception_type"),
                    "Exception",
                ),
                "exception_module": "builtins",
                "message": _string(crash.get("message")),
                "relation_to_next": None,
                "suppress_context": False,
                "file": _optional_string(crash.get("file")),
                "line": _optional_int(crash.get("line"), "$.crash.line"),
                "function": _optional_string(crash.get("function")),
                "traceback": list(crash.get("traceback") or []),
                "notes": [],
                "event_step": None,
            }
        )

    items[-1]["relation_to_next"] = None
    return {
        "items": items,
        "truncated": bool(raw_chain.get("truncated", False)),
        "cycle_detected": bool(raw_chain.get("cycle_detected", False)),
        "max_depth": _required_int(
            raw_chain.get("max_depth", 16),
            "$.exception_chain.max_depth",
        ),
    }


def _validate_exception_chain(value: Any) -> None:
    if not isinstance(value, dict):
        raise ReportSchemaError("must be an object", path="$.exception_chain")
    items = value.get("items")
    if not isinstance(items, list) or not items:
        raise ReportSchemaError(
            "must be a non-empty array",
            path="$.exception_chain.items",
        )
    if not isinstance(value.get("truncated"), bool):
        raise ReportSchemaError("must be a boolean", path="$.exception_chain.truncated")
    if not isinstance(value.get("cycle_detected"), bool):
        raise ReportSchemaError(
            "must be a boolean",
            path="$.exception_chain.cycle_detected",
        )
    if not isinstance(value.get("max_depth"), int) or isinstance(
        value.get("max_depth"),
        bool,
    ):
        raise ReportSchemaError("must be an integer", path="$.exception_chain.max_depth")

    for index, item in enumerate(items):
        path = f"$.exception_chain.items[{index}]"
        if not isinstance(item, dict):
            raise ReportSchemaError("must be an object", path=path)
        if not isinstance(item.get("index"), int) or isinstance(item.get("index"), bool):
            raise ReportSchemaError("must be an integer", path=f"{path}.index")
        for field in ("exception_type", "exception_module", "message"):
            if not isinstance(item.get(field), str):
                raise ReportSchemaError("must be a string", path=f"{path}.{field}")
        if item.get("relation_to_next") not in {None, "cause", "context"}:
            raise ReportSchemaError(
                "must be 'cause', 'context', or null",
                path=f"{path}.relation_to_next",
            )
        if not isinstance(item.get("suppress_context"), bool):
            raise ReportSchemaError(
                "must be a boolean",
                path=f"{path}.suppress_context",
            )
        if not isinstance(item.get("traceback"), list):
            raise ReportSchemaError("must be an array", path=f"{path}.traceback")
        if not isinstance(item.get("notes"), list) or not all(
            isinstance(note, str) for note in item.get("notes", [])
        ):
            raise ReportSchemaError(
                "must be an array of strings",
                path=f"{path}.notes",
            )
        event_step = item.get("event_step")
        if event_step is not None and (
            not isinstance(event_step, int) or isinstance(event_step, bool)
        ):
            raise ReportSchemaError(
                "must be an integer or null",
                path=f"{path}.event_step",
            )


def _normalize_crash_slice(value: Any) -> dict[str, Any]:
    result = _object_or_empty(value, "$.crash_slice")
    raw_steps = result.get("steps")
    if raw_steps is None:
        steps: list[int] = []
    elif isinstance(raw_steps, Sequence) and not isinstance(
        raw_steps, (str, bytes, bytearray)
    ):
        steps = sorted({_required_int(step, "$.crash_slice.steps[]") for step in raw_steps})
    else:
        raise ReportSchemaError("must be an array", path="$.crash_slice.steps")
    return {**result, "steps": steps}


def _normalize_events(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ReportSchemaError("must be an array", path="$.events")

    events: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ReportSchemaError("must be an object", path=f"$.events[{index}]")
        event = dict(item)
        path = f"$.events[{index}]"
        event["step"] = _required_int(event.get("step"), f"{path}.step")
        event["event"] = _string(event.get("event"), "line")
        event["file"] = _string(event.get("file"))
        event["line"] = _required_int(event.get("line", 0), f"{path}.line")
        event["function"] = _string(event.get("function"), "<module>")
        event["depth"] = _required_int(event.get("depth", 0), f"{path}.depth")
        event["locals"] = _object_or_empty(event.get("locals"), f"{path}.locals")
        event["changes"] = _object_or_empty(event.get("changes"), f"{path}.changes")
        if event.get("step_end") is not None:
            event["step_end"] = _required_int(event["step_end"], f"{path}.step_end")
        events.append(event)
    return events


def _normalize_trace_stats(value: Any) -> dict[str, Any]:
    stats = _object_or_empty(value, "$.trace_stats")
    defaults: dict[str, int | float] = {
        "max_events": 0,
        "total_events": 0,
        "retained_events": 0,
        "discarded_events": 0,
        "traced_files": 0,
        "excluded_events": 0,
        "duration_seconds": 0.0,
        "report_events": 0,
        "compressed_events": 0,
        "report_trimmed_events": 0,
        "report_size_bytes": 0,
    }
    return {**defaults, **stats}


def _normalize_sources(value: Any) -> dict[str, dict[str, Any]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ReportSchemaError("must be an object", path="$.sources")

    normalized: dict[str, dict[str, Any]] = {}
    for raw_path, source in value.items():
        if not isinstance(raw_path, str):
            raise ReportSchemaError("source paths must be strings", path="$.sources")
        lines = _source_lines(source, f"$.sources[{raw_path!r}]")
        normalized[raw_path] = {"lines": lines, "encoding": "utf-8"}
    return normalized


def _source_lines(value: Any, path: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return value.splitlines()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(line) for line in value]
    if isinstance(value, Mapping):
        for key in ("lines", "source", "content"):
            if key in value:
                return _source_lines(value[key], f"{path}.{key}")
    raise ReportSchemaError(
        "must be a string, an array of lines, or an object containing lines/source/content",
        path=path,
    )


def _build_integrity(document: Mapping[str, Any]) -> dict[str, Any]:
    canonical = {
        key: value
        for key, value in document.items()
        if key not in {"integrity", "translations"}
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    sources = document.get("sources") or {}
    return {
        "status": "ok",
        "algorithm": "sha256",
        "digest": hashlib.sha256(encoded).hexdigest(),
        "event_count": len(document.get("events") or []),
        "source_count": len(sources),
        "source_line_count": sum(len(source["lines"]) for source in sources.values()),
    }


def _object_or_empty(value: Any, path: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ReportSchemaError("must be an object", path=path)
    return dict(value)


def _optional_object(value: Any, path: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return _object_or_empty(value, path)


def _string_list(value: Any, path: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ReportSchemaError("must be an array", path=path)
    return [str(item) for item in value]


def _string(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def _optional_string(value: Any) -> str | None:
    return None if value is None else str(value)


def _required_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReportSchemaError("must be an integer", path=path)
    return value


def _optional_int(value: Any, path: str) -> int | None:
    if value is None:
        return None
    return _required_int(value, path)
