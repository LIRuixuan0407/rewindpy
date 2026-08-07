from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from rewindpy import __version__
from rewindpy.demos import create_demo_report
from rewindpy.report import write_report

_DATA_PATTERN = re.compile(
    r'<script id="rewind-data" type="application/json">(.*?)</script>',
    re.DOTALL,
)

_ADDRESS_PATTERN = re.compile(r"(?<= at )0x[0-9a-fA-F]+(?=>)")


def _stable_value(value: Any) -> Any:
    if isinstance(value, str):
        return _ADDRESS_PATTERN.sub("0x…", value)
    if isinstance(value, list):
        return [_stable_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _stable_value(item) for key, item in value.items()}
    return value


def _normalize_frame(frame: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(frame)
    if not normalized.get("project_file"):
        file_name = Path(str(normalized.get("file", ""))).name
        normalized["file"] = f"<runtime>/{file_name}" if file_name else "<runtime>"
    return normalized


def _stable_payload(report: Path) -> dict[str, Any]:
    html = report.read_text(encoding="utf-8")
    match = _DATA_PATTERN.search(html)
    if match is None:
        raise RuntimeError("generated report does not contain embedded data")
    payload = json.loads(match.group(1))
    payload.pop("translations", None)
    payload.pop("integrity", None)
    payload["project_root"] = "/demo/rewindpy"
    payload["target"] = "/demo/rewindpy/app.py"
    payload["rewindpy_version"] = __version__

    trace_stats = dict(payload.get("trace_stats") or {})
    trace_stats["duration_seconds"] = 0.0
    trace_stats["report_size_bytes"] = 0
    payload["trace_stats"] = trace_stats
    payload["events"] = _stable_value(payload.get("events") or [])

    crash = dict(payload.get("crash") or {})
    crash["traceback"] = [
        _normalize_frame(dict(frame)) for frame in crash.get("traceback", [])
    ]
    payload["crash"] = crash

    chain = dict(payload.get("exception_chain") or {})
    items = []
    for raw_item in chain.get("items", []):
        item = dict(raw_item)
        item["traceback"] = [
            _normalize_frame(dict(frame)) for frame in item.get("traceback", [])
        ]
        items.append(item)
    chain["items"] = items
    payload["exception_chain"] = chain
    return payload


def build_live_demo(output: Path) -> Path:
    output = output.resolve()
    with tempfile.TemporaryDirectory(prefix="rewindpy-live-demo-") as temp_dir:
        raw_report = Path(temp_dir) / "raw.html"
        create_demo_report("multi-file", output=raw_report, language="en")
        write_report(output, _stable_payload(raw_report))
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the deterministic GitHub Pages demo.")
    parser.add_argument("--output", type=Path, default=Path("docs/index.html"))
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        if not args.output.is_file():
            print(f"missing live demo: {args.output}")
            return 1
        with tempfile.TemporaryDirectory(prefix="rewindpy-live-demo-check-") as temp_dir:
            candidate = Path(temp_dir) / "index.html"
            build_live_demo(candidate)
            if candidate.read_bytes() != args.output.read_bytes():
                print("docs/index.html is stale; run python scripts/build_live_demo.py")
                return 1
        print("docs/index.html is current")
        return 0

    build_live_demo(args.output)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
