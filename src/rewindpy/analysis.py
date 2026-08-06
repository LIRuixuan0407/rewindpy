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
