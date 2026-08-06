from __future__ import annotations

import tempfile
import webbrowser
from pathlib import Path

from .i18n import text
from .runner import run_target

_DEMOS = {
    "none-origin": '''def find_user(user_id):
    users = {"100": {"name": "Alice"}}
    return users.get(user_id)


def render_profile(user):
    return f"Welcome, {user.get('name').upper()}"


current_user = find_user("999")
print(render_profile(current_user))
''',
    "key-error": '''def normalize_user(data):
    normalized = dict(data)
    normalized["userid"] = normalized.pop("user_id")
    return normalized


user = normalize_user({"user_id": "42", "name": "Alice"})
print(user["user_id"])
''',
    "exception-chain": '''import json


class StartupError(RuntimeError):
    pass


def parse_config(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        if hasattr(exc, "add_note"):
            exc.add_note("The built-in demo intentionally uses malformed JSON.")
        raise ValueError("configuration is not valid JSON") from exc


def start_application():
    try:
        return parse_config('{"port": 8000,}')
    except ValueError as exc:
        raise StartupError("application startup failed") from exc


start_application()
''',
    "crash-slice": '''def warm_up():
    total = 0
    for value in range(80):
        total += value
    return total


def normalize_user(data):
    normalized = dict(data)
    normalized["userid"] = normalized.pop("user_id")
    return normalized


warm_up()
user = normalize_user({"user_id": "42"})
print(user["user_id"])
''',
}


def demo_names() -> tuple[str, ...]:
    return tuple(_DEMOS)


def create_demo_report(
    kind: str,
    *,
    output: Path,
    max_events: int = 5_000,
    open_report: bool = False,
    language: str = "en",
) -> Path:
    try:
        source = _DEMOS[kind]
    except KeyError as exc:
        raise ValueError(text(language, "unknown_demo", kind=kind)) from exc

    output = output.resolve()
    with tempfile.TemporaryDirectory(prefix="rewindpy-demo-") as temp_dir:
        target = Path(temp_dir) / f"{kind.replace('-', '_')}.py"
        target.write_text(source, encoding="utf-8")
        run_target(
            target,
            [],
            output=output,
            max_events=max_events,
            language=language,
        )

    if not output.is_file():
        raise RuntimeError(text(language, "demo_failed"))
    if open_report:
        webbrowser.open(output.as_uri())
    return output
