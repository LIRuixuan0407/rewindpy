from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_pytest(project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    source = str(ROOT / "src")
    environment["PYTHONPATH"] = source + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "pytest", *arguments],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_plugin_does_nothing_without_flag(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    result = _run_pytest(tmp_path, "-q")
    assert result.returncode == 0
    assert not (tmp_path / ".rewindpy").exists()


def test_plugin_generates_report_only_for_failure(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert True\n\n"
        "def test_bad():\n    value = None\n    assert value.name == 'Ada'\n"
    )
    result = _run_pytest(tmp_path, "--rewind", "--rewind-lang", "zh", "-q")
    reports = list((tmp_path / ".rewindpy").glob("*.html"))
    assert result.returncode == 1
    assert len(reports) == 1
    assert "test_bad" in reports[0].name
    content = reports[0].read_text(encoding="utf-8")
    assert "RewindPy" in content
    assert "test_bad" in result.stdout


def test_plugin_supports_custom_directory_and_unique_parameter_names(tmp_path: Path) -> None:
    (tmp_path / "test_params.py").write_text(
        "import pytest\n\n"
        "@pytest.mark.parametrize('value', [1, 2])\n"
        "def test_value(value):\n    assert value == 0\n"
    )
    result = _run_pytest(tmp_path, "--rewind", "--rewind-dir", "reports", "-q")
    reports = list((tmp_path / "reports").glob("*.html"))
    assert result.returncode == 1
    assert len(reports) == 2
    assert reports[0].name != reports[1].name
