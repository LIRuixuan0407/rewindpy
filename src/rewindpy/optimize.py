from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Sequence


def compress_repeated_cycles(
    events: Sequence[dict[str, Any]],
    *,
    max_pattern: int = 8,
    min_repeats: int = 3,
) -> tuple[list[dict[str, Any]], int]:
    """Collapse repeated quiet execution cycles for the report timeline.

    Analysis still runs against the original event stream. Only the report's
    all-events view is compressed, so crash evidence remains untouched.
    """
    source = list(events)
    result: list[dict[str, Any]] = []
    index = 0
    compressed = 0

    while index < len(source):
        match: tuple[int, int] | None = None
        remaining = len(source) - index
        for pattern_size in range(1, min(max_pattern, remaining // min_repeats) + 1):
            pattern = source[index : index + pattern_size]
            if not all(_is_compressible(event) for event in pattern):
                continue
            repeats = 1
            while index + (repeats + 1) * pattern_size <= len(source):
                candidate = source[
                    index + repeats * pattern_size : index + (repeats + 1) * pattern_size
                ]
                if [_signature(event) for event in candidate] != [
                    _signature(event) for event in pattern
                ]:
                    break
                if not all(_is_compressible(event) for event in candidate):
                    break
                repeats += 1
            if repeats >= min_repeats:
                match = pattern_size, repeats
                break

        if match is None:
            result.append(deepcopy(source[index]))
            index += 1
            continue

        pattern_size, repeats = match
        block = source[index : index + pattern_size * repeats]
        first = block[0]
        last = block[-1]
        summary = deepcopy(last)
        summary.update(
            {
                "event": "repeat",
                "step": first["step"],
                "step_end": last["step"],
                "repeat_count": repeats,
                "pattern_size": pattern_size,
                "source_steps": [event["step"] for event in block],
                "changes": {},
                "exception_type": None,
                "exception_message": None,
            }
        )
        result.append(summary)
        compressed += len(block) - 1
        index += len(block)

    return result, compressed


def fit_report_budget(
    payload: dict[str, Any],
    *,
    max_bytes: int,
    protected_steps: set[int] | None = None,
) -> tuple[dict[str, Any], int]:
    """Trim low-priority report events until the embedded JSON fits a budget."""
    document = deepcopy(payload)
    events = list(document.get("events") or [])
    protected = set(protected_steps or ())
    removed = 0

    def encoded_size() -> int:
        return len(json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    if max_bytes <= 0 or encoded_size() <= max_bytes:
        return document, 0

    while len(events) > 1 and encoded_size() > max_bytes:
        removable = [
            index
            for index, event in enumerate(events)
            if not _event_is_protected(event, protected)
        ]
        if not removable:
            break
        # Remove older, low-priority events first while retaining a useful spread.
        selected = removable[::2] or removable[:1]
        selected_set = set(selected)
        events = [event for index, event in enumerate(events) if index not in selected_set]
        removed += len(selected)
        document["events"] = events

    return document, removed


def event_contains_step(event: dict[str, Any], step: int) -> bool:
    if int(event.get("step", -1)) == int(step):
        return True
    if int(event.get("step_end", -1)) == int(step):
        return True
    return int(step) in {int(value) for value in event.get("source_steps") or []}


def _event_is_protected(event: dict[str, Any], protected_steps: set[int]) -> bool:
    if event.get("exception_type") or event.get("event") == "exception":
        return True
    return any(event_contains_step(event, step) for step in protected_steps)


def _is_compressible(event: dict[str, Any]) -> bool:
    return event.get("event") == "line" and not event.get("exception_type")


def _signature(event: dict[str, Any]) -> tuple[Any, ...]:
    return (
        event.get("event"),
        event.get("file"),
        event.get("line"),
        event.get("function"),
        event.get("depth"),
        tuple(sorted((event.get("changes") or {}).keys())),
    )
