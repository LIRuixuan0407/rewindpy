from __future__ import annotations

import json
import platform
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from . import __version__
from .demos import create_demo_report
from .i18n import text
from .schema import REPORT_SCHEMA_VERSION, verify_report_integrity

_MINIMUM_PYTHON = (3, 10)


@dataclass(frozen=True)
class DoctorResult:
    rewindpy_version: str
    python_version: str
    python_implementation: str
    platform: str
    virtual_environment: bool
    supported_python: bool
    working_directory_writable: bool
    demo_smoke_test: bool

    @property
    def ready(self) -> bool:
        return (
            self.supported_python
            and self.working_directory_writable
            and self.demo_smoke_test
        )

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "ready": self.ready}


def _working_directory_is_writable() -> bool:
    try:
        with tempfile.NamedTemporaryFile(dir=Path.cwd()):
            pass
    except OSError:
        return False
    return True


def _demo_smoke_test() -> bool:
    try:
        with tempfile.TemporaryDirectory(prefix="rewindpy-doctor-") as temp_dir:
            report = Path(temp_dir) / "doctor-report.html"
            create_demo_report(
                "none-origin",
                output=report,
                max_events=1_000,
                language="en",
            )
            html = report.read_text(encoding="utf-8")
            start = html.index('<script id="rewind-data" type="application/json">')
            start = html.index(">", start) + 1
            end = html.index("</script>", start)
            payload = json.loads(html[start:end])
            verify_report_integrity(payload)
    except (OSError, RuntimeError, ValueError):
        return False
    return (
        'id="sliceView"' in html
        and payload["schema_version"] == REPORT_SCHEMA_VERSION
        and payload["analysis"]["kind"] == "none-value-origin"
    )


def run_doctor() -> DoctorResult:
    return DoctorResult(
        rewindpy_version=__version__,
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        platform=platform.platform(),
        virtual_environment=sys.prefix != sys.base_prefix,
        supported_python=sys.version_info >= _MINIMUM_PYTHON,
        working_directory_writable=_working_directory_is_writable(),
        demo_smoke_test=_demo_smoke_test(),
    )


def format_doctor_report(result: DoctorResult, language: str) -> str:
    def mark(value: bool) -> str:
        return text(language, "pass" if value else "fail")

    environment = text(language, "yes" if result.virtual_environment else "no")
    status = text(language, "doctor_ready" if result.ready else "doctor_not_ready")
    return "\n".join(
        [
            text(language, "doctor_title"),
            f"{text(language, 'doctor_status')}: {status}",
            f"RewindPy: {result.rewindpy_version}",
            (
                f"{text(language, 'doctor_python')}: {result.python_version} "
                f"({result.python_implementation})"
            ),
            f"{text(language, 'doctor_platform')}: {result.platform}",
            f"{text(language, 'doctor_virtualenv')}: {environment}",
            f"{text(language, 'doctor_supported')}: {mark(result.supported_python)}",
            (
                f"{text(language, 'doctor_writable')}: "
                f"{mark(result.working_directory_writable)}"
            ),
            f"{text(language, 'doctor_demo')}: {mark(result.demo_smoke_test)}",
        ]
    )


def format_doctor_json(result: DoctorResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)
