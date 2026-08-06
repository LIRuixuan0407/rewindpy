from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_SECRET_NAMES = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
}


@dataclass(slots=True)
class SerializationConfig:
    max_depth: int = 2
    max_items: int = 20
    max_string_length: int = 240
    secret_names: frozenset[str] = frozenset(DEFAULT_SECRET_NAMES)


class SafeSerializer:
    def __init__(self, config: SerializationConfig | None = None) -> None:
        self.config = config or SerializationConfig()

    def is_secret_name(self, name: object) -> bool:
        normalized = str(name).lower().replace("-", "_")
        return any(secret in normalized for secret in self.config.secret_names)

    def serialize_locals(self, values: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, value in sorted(values.items()):
            if name.startswith("__") and name.endswith("__"):
                continue
            result[name] = "<redacted>" if self.is_secret_name(name) else self.serialize(value)
        return result

    def redact_source_line(self, line: str) -> str:
        """Hide an entire source line when it contains a secret-like identifier.

        This intentionally favors safety over perfect source fidelity because a
        self-contained report can otherwise expose hard-coded credentials.
        """
        lowered = line.lower().replace("-", "_")
        if any(secret in lowered for secret in self.config.secret_names):
            indentation = line[: len(line) - len(line.lstrip())]
            return indentation + "# <redacted source line>"
        return line

    def serialize(self, value: Any, *, depth: int = 0) -> Any:
        if value is None or isinstance(value, (bool, int, float)):
            return value

        if isinstance(value, str):
            return self._truncate(value)

        if isinstance(value, bytes):
            return f"<bytes {len(value)}>"

        if depth >= self.config.max_depth:
            return self._safe_repr(value)

        if isinstance(value, dict):
            serialized: dict[str, Any] = {}
            for index, (key, item) in enumerate(value.items()):
                if index >= self.config.max_items:
                    serialized["…"] = f"{len(value) - self.config.max_items} more item(s)"
                    break
                key_text = self._truncate(str(key))
                serialized[key_text] = (
                    "<redacted>"
                    if self.is_secret_name(key)
                    else self.serialize(item, depth=depth + 1)
                )
            return serialized

        if isinstance(value, (list, tuple, set, frozenset)):
            items = list(value)
            serialized_items = [
                self.serialize(item, depth=depth + 1)
                for item in items[: self.config.max_items]
            ]
            if len(items) > self.config.max_items:
                serialized_items.append(f"… {len(items) - self.config.max_items} more item(s)")
            return serialized_items

        return self._safe_repr(value)

    def _safe_repr(self, value: Any) -> str:
        try:
            rendered = repr(value)
        except Exception as exc:  # pragma: no cover - defensive fallback
            rendered = f"<{type(value).__name__} repr failed: {type(exc).__name__}>"
        return self._truncate(rendered)

    def _truncate(self, value: str) -> str:
        limit = self.config.max_string_length
        if len(value) <= limit:
            return value
        return value[:limit] + f"… <{len(value) - limit} chars truncated>"
