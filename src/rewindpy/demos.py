from __future__ import annotations

import importlib
import sys
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

_MULTI_FILE_DEMOS: dict[str, tuple[str, dict[str, str]]] = {
    "multi-file": (
        "app.py",
        {
            "app.py": '''from service import start_application


start_application()
''',
            "service.py": '''from config_loader import load_config


class StartupError(RuntimeError):
    pass


def start_application():
    try:
        config = load_config()
        return config["database"]["url"]
    except ValueError as exc:
        raise StartupError("application startup failed") from exc
''',
            "config_loader.py": '''import json


def load_config():
    raw = '{"database": {"url": "sqlite:///demo.db",}}'
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        if hasattr(exc, "add_note"):
            exc.add_note("The multi-file demo intentionally uses malformed JSON.")
        raise ValueError("configuration is not valid JSON") from exc
''',
        },
    ),
}


def demo_names() -> tuple[str, ...]:
    return tuple((*_DEMOS, *_MULTI_FILE_DEMOS))


def create_demo_report(
    kind: str,
    *,
    output: Path,
    max_events: int = 5_000,
    open_report: bool = False,
    language: str = "en",
) -> Path:
    output = output.resolve()
    with tempfile.TemporaryDirectory(prefix="rewindpy-demo-") as temp_dir:
        root = Path(temp_dir)
        if kind in _MULTI_FILE_DEMOS:
            entrypoint, files = _MULTI_FILE_DEMOS[kind]
            for relative, source in files.items():
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(source, encoding="utf-8")
            target = root / entrypoint
        else:
            try:
                source = _DEMOS[kind]
            except KeyError as exc:
                raise ValueError(text(language, "unknown_demo", kind=kind)) from exc
            target = root / f"{kind.replace('-', '_')}.py"
            target.write_text(source, encoding="utf-8")
        module_names: set[str] = set()
        if kind in _MULTI_FILE_DEMOS:
            module_names = {
                ".".join(Path(relative).with_suffix("").parts)
                for relative in files
                if relative != entrypoint
            }
        previous_modules = {name: sys.modules.get(name) for name in module_names}
        for name in module_names:
            sys.modules.pop(name, None)
        importlib.invalidate_caches()
        try:
            run_target(
                target,
                [],
                output=output,
                max_events=max_events,
                language=language,
            )
        finally:
            for name in module_names:
                sys.modules.pop(name, None)
                previous = previous_modules[name]
                if previous is not None:
                    sys.modules[name] = previous
            importlib.invalidate_caches()

    if not output.is_file():
        raise RuntimeError(text(language, "demo_failed"))
    if open_report:
        webbrowser.open(output.as_uri())
    return output
