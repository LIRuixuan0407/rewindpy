from __future__ import annotations

import ast
from difflib import get_close_matches
from typing import Any


def analyze_crash(
    events: list[dict[str, Any]],
    crash: dict[str, Any],
) -> dict[str, Any] | None:
    """Find a likely earlier state change that explains the crash.

    The first MVP analysis focuses on KeyError because it has a concrete,
    traceable failure condition: a mapping key is missing at the crash site.
    """
    if crash.get("exception_type") != "KeyError":
        return None

    missing_key = _parse_keyerror_key(str(crash.get("message", "")))
    if missing_key is None:
        return None

    crash_step = _last_exception_step(events) or (events[-1]["step"] if events else 0)

    for event in reversed(events):
        for variable_name, change in (event.get("changes") or {}).items():
            before = change.get("before")
            after = change.get("after")
            removed = _find_removed_key(before, after, missing_key)
            if removed is None:
                continue

            container_path, before_mapping, after_mapping = removed
            added_keys = sorted(
                str(key) for key in after_mapping.keys() - before_mapping.keys()
            )
            likely_replacement = _closest_key(str(missing_key), added_keys)
            origin_step = int(event.get("step", 0))
            distance = max(0, crash_step - origin_step)
            variable_path = variable_name
            if container_path:
                variable_path += "".join(f"[{part!r}]" for part in container_path)

            return {
                "kind": "missing-key-origin",
                "summary": _build_summary(
                    str(missing_key), distance, variable_path, likely_replacement
                ),
                "missing_key": missing_key,
                "origin_step": origin_step,
                "crash_step": crash_step,
                "steps_before_crash": distance,
                "file": event.get("file"),
                "line": event.get("change_line") or event.get("line"),
                "function": event.get("function"),
                "variable": variable_path,
                "before": before_mapping,
                "after": after_mapping,
                "added_keys": added_keys,
                "likely_replacement": likely_replacement,
            }

    return None


def _parse_keyerror_key(message: str) -> Any | None:
    if not message:
        return None
    try:
        return ast.literal_eval(message)
    except (ValueError, SyntaxError):
        stripped = message.strip().strip("'\"")
        return stripped or None


def _last_exception_step(events: list[dict[str, Any]]) -> int | None:
    for event in reversed(events):
        if event.get("event") == "exception":
            return int(event.get("step", 0))
    return None


def _find_removed_key(
    before: Any,
    after: Any,
    key: Any,
    path: tuple[Any, ...] = (),
) -> tuple[tuple[Any, ...], dict[Any, Any], dict[Any, Any]] | None:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return None

    if key in before and key not in after:
        return path, before, after

    for shared_key in before.keys() & after.keys():
        nested = _find_removed_key(
            before[shared_key], after[shared_key], key, (*path, shared_key)
        )
        if nested is not None:
            return nested
    return None


def _closest_key(missing_key: str, added_keys: list[str]) -> str | None:
    if not added_keys:
        return None
    matches = get_close_matches(missing_key, added_keys, n=1, cutoff=0.45)
    return matches[0] if matches else None


def _build_summary(
    missing_key: str,
    distance: int,
    variable: str,
    likely_replacement: str | None,
) -> str:
    step_word = "step" if distance == 1 else "steps"
    summary = (
        f"Key {missing_key!r} disappeared from {variable} "
        f"{distance} {step_word} before the crash."
    )
    if likely_replacement:
        summary += f" It may have been renamed to {likely_replacement!r}."
    return summary


def build_crash_slice(
    events: list[dict[str, Any]],
    crash: dict[str, Any],
    analysis: dict[str, Any] | None = None,
    *,
    context_steps: int = 30,
) -> dict[str, Any]:
    """Select a compact set of events that tells the crash story.

    The slice keeps:
    - the final ``context_steps`` leading into the innermost crash event;
    - call-site checkpoints for project frames in the traceback;
    - every propagated exception event;
    - the value-origin event (plus one neighboring event on each side).

    Full execution history remains in the report and can be restored with the
    "All Events" toggle. The slice stores step numbers instead of duplicating
    event payloads.
    """
    if not events:
        return {
            "steps": [],
            "total_events": 0,
            "shown_events": 0,
            "omitted_events": 0,
            "context_steps": max(0, context_steps),
        }

    context_steps = max(1, context_steps)
    anchor_index = _find_crash_anchor(events, crash)
    relevant_indices: set[int] = set(
        range(max(0, anchor_index - context_steps + 1), anchor_index + 1)
    )

    # Keep exception propagation visible even when it occurs after the
    # innermost crash event selected as the anchor.
    relevant_indices.update(
        index for index, event in enumerate(events) if event.get("event") == "exception"
    )

    # Add two lightweight checkpoints for every project frame in the traceback:
    # the active call and the line represented by the traceback frame.
    for frame in crash.get("traceback") or []:
        if not frame.get("project_file", True):
            continue
        signature = (frame.get("file"), frame.get("function"))
        checkpoint = _find_frame_checkpoint(
            events,
            signature=signature,
            line=frame.get("line"),
            before_or_at=anchor_index,
        )
        if checkpoint is None:
            continue
        relevant_indices.add(checkpoint)
        call_index = _find_active_call(
            events,
            signature=signature,
            before_or_at=checkpoint,
        )
        if call_index is not None:
            relevant_indices.add(call_index)

    origin_step = (analysis or {}).get("origin_step")
    if origin_step is not None:
        origin_index = next(
            (
                index
                for index, event in enumerate(events)
                if event.get("step") == origin_step
            ),
            None,
        )
        if origin_index is not None:
            relevant_indices.update(
                range(max(0, origin_index - 1), min(len(events), origin_index + 2))
            )

    ordered_indices = sorted(relevant_indices)
    steps = [int(events[index].get("step", index + 1)) for index in ordered_indices]
    return {
        "steps": steps,
        "total_events": len(events),
        "shown_events": len(steps),
        "omitted_events": len(events) - len(steps),
        "context_steps": context_steps,
        "anchor_step": int(events[anchor_index].get("step", anchor_index + 1)),
    }


def _find_crash_anchor(
    events: list[dict[str, Any]], crash: dict[str, Any]
) -> int:
    expected_file = crash.get("file")
    expected_function = crash.get("function")
    expected_type = crash.get("exception_type")

    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        if event.get("event") != "exception":
            continue
        if expected_file and event.get("file") != expected_file:
            continue
        if expected_function and event.get("function") != expected_function:
            continue
        if expected_type and event.get("exception_type") != expected_type:
            continue
        return index

    for index in range(len(events) - 1, -1, -1):
        if events[index].get("event") == "exception":
            return index
    return len(events) - 1


def _find_frame_checkpoint(
    events: list[dict[str, Any]],
    *,
    signature: tuple[Any, Any],
    line: Any,
    before_or_at: int,
) -> int | None:
    fallback: int | None = None
    for index in range(before_or_at, -1, -1):
        event = events[index]
        if (event.get("file"), event.get("function")) != signature:
            continue
        if fallback is None:
            fallback = index
        if line is not None and event.get("line") == line:
            return index
    return fallback


def _find_active_call(
    events: list[dict[str, Any]],
    *,
    signature: tuple[Any, Any],
    before_or_at: int,
) -> int | None:
    for index in range(before_or_at, -1, -1):
        event = events[index]
        if (event.get("file"), event.get("function")) != signature:
            continue
        if event.get("event") == "call":
            return index
    return None
