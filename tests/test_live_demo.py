from __future__ import annotations

import json
import re
from pathlib import Path

from rewindpy.schema import verify_report_integrity
from scripts.build_live_demo import build_live_demo


def _payload(path: Path) -> dict:
    match = re.search(
        r'<script id="rewind-data" type="application/json">(.*?)</script>',
        path.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert match is not None
    return json.loads(match.group(1))


def test_live_demo_is_deterministic_and_multi_file(tmp_path: Path) -> None:
    first = build_live_demo(tmp_path / "first.html")
    second = build_live_demo(tmp_path / "second.html")

    assert first.read_bytes() == second.read_bytes()
    payload = _payload(first)
    verify_report_integrity(payload)
    assert payload["project_root"] == "/demo/rewindpy"
    assert sorted(payload["sources"]) == ["app.py", "config_loader.py", "service.py"]
    assert len(payload["exception_chain"]["items"]) == 3
