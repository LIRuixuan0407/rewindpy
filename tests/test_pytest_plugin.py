from __future__ import annotations

import os
import subprocess
import sys
from importlib.metadata import entry_points
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_pytest(project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    source = str(ROOT / "src")
    environment["PYTHONPATH"] = source + os.pathsep + environment.get("PYTHONPATH", "")
    plugin_args: list[str] = []
    registered = any(
        point.name == "rewindpy"
        for point in entry_points(group="pytest11")
    )
    if not registered:
        plugin_args = ["-p", "rewindpy.pytest_plugin"]
    return subprocess.run(
        [sys.executable, "-m", "pytest", *plugin_args, *arguments],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
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
    reports = [path for path in (tmp_path / ".rewindpy").glob("*.html") if path.name != "index.html"]
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
    reports = [path for path in (tmp_path / "reports").glob("*.html") if path.name != "index.html"]
    assert result.returncode == 1
    assert len(reports) == 2
    assert reports[0].name != reports[1].name


def test_plugin_prints_summary_when_all_tests_pass(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    result = _run_pytest(tmp_path, "--rewind", "--rewind-lang", "en", "-q")
    assert result.returncode == 0
    assert "Tests observed: 1" in result.stdout
    assert "Reports generated: 0" in result.stdout
    assert "all tests passed" in result.stdout


def test_plugin_generates_bilingual_report_index(tmp_path: Path) -> None:
    (tmp_path / "test_bad.py").write_text("def test_bad():\n    value = None\n    assert value.name == 'Ada'\n")
    result = _run_pytest(tmp_path, "--rewind", "--rewind-lang", "zh", "-q")
    index = tmp_path / ".rewindpy" / "index.html"
    assert result.returncode == 1
    assert index.exists()
    content = index.read_text(encoding="utf-8")
    assert "RewindPy 测试失败报告" in content
    assert "test_bad" in content
    assert "报告索引: .rewindpy/index.html" in result.stdout
