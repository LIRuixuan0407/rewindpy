from __future__ import annotations

import ast
import re
from difflib import get_close_matches
from typing import Any

from .i18n import text


_NONE_ATTRIBUTE_PATTERN = re.compile(
    r"'NoneType' object has no attribute '([^']+)'"
)
_NOT_SET = "<not set>"


def analyze_crash(
    events: list[dict[str, Any]],
    crash: dict[str, Any],
    *,
    language: str = "en",
) -> dict[str, Any] | None:
    """Find a likely earlier state change that explains the crash.

    Supported analyses currently include:
    - a dictionary key removed or probably renamed before ``KeyError``;
    - a local value that became ``None`` before a NoneType ``AttributeError``.
    """
    exception_type = crash.get("exception_type")
    if exception_type == "KeyError":
        return _analyze_keyerror(events, crash, language)
    if exception_type == "AttributeError":
        return _analyze_none_attribute_error(events, crash, language)
    return None


def _analyze_keyerror(
    events: list[dict[str, Any]],
    crash: dict[str, Any],
    language: str,
) -> dict[str, Any] | None:
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

            title_i18n = {
                code: text(code, "missing_key_title") for code in ("en", "zh")
            }
            summary_i18n = {
                code: _build_key_summary(
                    str(missing_key), distance, variable_path, likely_replacement, code
                )
                for code in ("en", "zh")
            }
            return {
                "kind": "missing-key-origin",
                "title": title_i18n[language],
                "summary": summary_i18n[language],
                "title_i18n": title_i18n,
                "summary_i18n": summary_i18n,
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
                "confidence": 0.9 if likely_replacement else 0.8,
            }

    return None


def _analyze_none_attribute_error(
    events: list[dict[str, Any]],
    crash: dict[str, Any],
    language: str,
) -> dict[str, Any] | None:
    attribute = _parse_none_attribute(str(crash.get("message", "")))
    if attribute is None or not events:
        return None

    crash_index = _find_crash_anchor(events, crash)
    crash_event = events[crash_index]
    crash_source = _matching_traceback_source(crash)
    variable = _select_none_variable(
        crash_event.get("locals") or {}, crash_source, attribute
    )
    if variable is None:
        return None

    traceback_names = _traceback_local_names(crash)
    assignment = _find_none_assignment(
        events,
        before_or_at=crash_index,
        preferred_names=traceback_names | {variable},
        crash_file=crash.get("file"),
        crash_function=crash.get("function"),
        crash_variable=variable,
    )

    producer: tuple[int, dict[str, Any]] | None = None
    if assignment is not None:
        assignment_index, assignment_event, upstream_variable = assignment
        producer = _find_none_return_producer(
            events,
            before_index=assignment_index,
            assignment_depth=assignment_event.get("depth"),
        )
    else:
        upstream_variable = variable
        assignment_index = crash_index
        assignment_event = crash_event
        producer = _find_none_return_producer(
            events,
            before_index=crash_index,
            assignment_depth=crash_event.get("depth"),
        )

    if producer is not None:
        origin_index, origin_event = producer
        reason = "returned-none"
        producer_function = origin_event.get("function")
    elif assignment is not None:
        origin_index = assignment_index
        origin_event = assignment_event
        reason = "assigned-none"
        producer_function = None
    else:
        # We know which crash variable is None, but without an earlier assignment
        # or return event we cannot make a trustworthy origin claim.
        return None

    crash_step = int(crash_event.get("step", 0))
    origin_step = int(origin_event.get("step", 0))
    distance = max(0, crash_step - origin_step)
    title_i18n = {code: text(code, "none_title") for code in ("en", "zh")}
    summary_i18n = {
        code: _build_none_summary(
            variable=variable,
            upstream_variable=upstream_variable,
            producer_function=producer_function,
            distance=distance,
            language=code,
        )
        for code in ("en", "zh")
    }

    return {
        "kind": "none-value-origin",
        "title": title_i18n[language],
        "summary": summary_i18n[language],
        "title_i18n": title_i18n,
        "summary_i18n": summary_i18n,
        "attribute": attribute,
        "variable": variable,
        "upstream_variable": upstream_variable,
        "origin_step": origin_step,
        "crash_step": crash_step,
        "steps_before_crash": distance,
        "file": origin_event.get("file"),
        "line": (
            origin_event.get("line")
            if reason == "returned-none"
            else origin_event.get("change_line") or origin_event.get("line")
        ),
        "function": origin_event.get("function"),
        "producer_function": producer_function,
        "reason": reason,
        "confidence": 0.9 if producer_function else 0.75,
    }


def _parse_keyerror_key(message: str) -> Any | None:
    if not message:
        return None
    try:
        return ast.literal_eval(message)
    except (ValueError, SyntaxError):
        stripped = message.strip().strip("'\"")
        return stripped or None


def _parse_none_attribute(message: str) -> str | None:
    match = _NONE_ATTRIBUTE_PATTERN.fullmatch(message.strip())
    return match.group(1) if match else None


def _matching_traceback_source(crash: dict[str, Any]) -> str:
    expected_file = crash.get("file")
    expected_function = crash.get("function")
    for frame in reversed(crash.get("traceback") or []):
        if expected_file and frame.get("file") != expected_file:
            continue
        if expected_function and frame.get("function") != expected_function:
            continue
        return str(frame.get("source") or "")
    return ""


def _select_none_variable(
    locals_snapshot: dict[str, Any],
    source: str,
    attribute: str,
) -> str | None:
    none_names = {
        name for name, value in locals_snapshot.items() if value is None
    }
    if not none_names:
        return None

    source_candidates = _attribute_base_names(source, attribute)
    matched = sorted(none_names & source_candidates)
    if len(matched) == 1:
        return matched[0]
    if len(none_names) == 1:
        return next(iter(none_names))
    return None


def _attribute_base_names(source: str, attribute: str) -> set[str]:
    if not source:
        return set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        pattern = re.compile(rf"\b([A-Za-z_]\w*)\s*\.\s*{re.escape(attribute)}\b")
        return set(pattern.findall(source))

    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr != attribute:
            continue
        root = node.value
        while isinstance(root, (ast.Attribute, ast.Subscript, ast.Call)):
            if isinstance(root, ast.Attribute):
                root = root.value
            elif isinstance(root, ast.Subscript):
                root = root.value
            else:
                break
        if isinstance(root, ast.Name):
            names.add(root.id)
    return names


def _traceback_local_names(crash: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for frame in crash.get("traceback") or []:
        if not frame.get("project_file", True):
            continue
        source = str(frame.get("source") or "")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            names.update(re.findall(r"\b[A-Za-z_]\w*\b", source))
            continue
        names.update(
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        )
    return names


def _find_none_assignment(
    events: list[dict[str, Any]],
    *,
    before_or_at: int,
    preferred_names: set[str],
    crash_file: Any,
    crash_function: Any,
    crash_variable: str,
) -> tuple[int, dict[str, Any], str] | None:
    candidates: list[tuple[tuple[int, int, int], int, dict[str, Any], str]] = []
    for index in range(before_or_at, -1, -1):
        event = events[index]
        for name, change in (event.get("changes") or {}).items():
            if change.get("after") is not None:
                continue
            if change.get("before") is None:
                continue

            is_parameter_binding = (
                event.get("event") == "call"
                and event.get("file") == crash_file
                and event.get("function") == crash_function
                and name == crash_variable
            )
            outside_crash_frame = not (
                event.get("file") == crash_file
                and event.get("function") == crash_function
            )
            rank = (
                1 if name in preferred_names else 0,
                1 if outside_crash_frame else 0,
                0 if is_parameter_binding else 1,
            )
            candidates.append((rank, index, event, name))

    if not candidates:
        return None
    _, index, event, name = max(candidates, key=lambda item: (item[0], item[1]))
    return index, event, name


def _find_none_return_producer(
    events: list[dict[str, Any]],
    *,
    before_index: int,
    assignment_depth: Any,
    max_gap: int = 8,
) -> tuple[int, dict[str, Any]] | None:
    minimum = max(-1, before_index - max_gap - 1)
    for index in range(before_index - 1, minimum, -1):
        event = events[index]
        if event.get("event") != "return" or event.get("return_value") is not None:
            continue
        event_depth = event.get("depth")
        if (
            isinstance(assignment_depth, int)
            and isinstance(event_depth, int)
            and event_depth <= assignment_depth
        ):
            continue
        return index, event
    return None


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


def _build_key_summary(
    missing_key: str,
    distance: int,
    variable: str,
    likely_replacement: str | None,
    language: str,
) -> str:
    step_word = text(
        language,
        "step_singular" if distance == 1 else "step_plural",
    )
    summary = text(
        language,
        "missing_key_summary",
        key=missing_key,
        variable=variable,
        distance=distance,
        step_word=step_word,
    )
    if likely_replacement:
        summary += text(
            language,
            "missing_key_rename",
            replacement=likely_replacement,
        )
    return summary


def _build_none_summary(
    *,
    variable: str,
    upstream_variable: str,
    producer_function: Any,
    distance: int,
    language: str,
) -> str:
    step_word = text(
        language,
        "step_singular" if distance == 1 else "step_plural",
    )
    if producer_function:
        if upstream_variable != variable:
            return text(
                language,
                "none_summary_through",
                variable=variable,
                upstream=upstream_variable,
                producer=producer_function,
                distance=distance,
                step_word=step_word,
            )
        return text(
            language,
            "none_summary_from",
            variable=variable,
            producer=producer_function,
            distance=distance,
            step_word=step_word,
        )
    return text(
        language,
        "none_summary_became",
        variable=variable,
        distance=distance,
        step_word=step_word,
    )


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

    relevant_indices.update(
        index for index, event in enumerate(events) if event.get("event") == "exception"
    )

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
