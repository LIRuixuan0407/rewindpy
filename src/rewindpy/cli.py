from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .demos import create_demo_report, demo_names
from .doctor import format_doctor_json, format_doctor_report, run_doctor
from .i18n import normalize_language, text
from .runner import run_target


def _extract_language(argv: list[str]) -> tuple[str, list[str]]:
    value: str | None = None
    remaining: list[str] = []
    index = 0
    while index < len(argv):
        item = argv[index]
        if item == "--lang":
            if index + 1 >= len(argv):
                raise ValueError(None)
            value = argv[index + 1]
            index += 2
            continue
        if item.startswith("--lang="):
            value = item.split("=", 1)[1]
            index += 1
            continue
        remaining.append(item)
        index += 1
    return normalize_language(value), remaining


def build_parser(language: str = "en") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rewindpy",
        description=text(language, "cli_description"),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--lang",
        metavar="{auto,en,zh}",
        default="auto",
        help=text(language, "lang_help"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help=text(language, "run_help"),
        description=text(language, "run_help"),
    )
    run.add_argument("target", type=Path, help=text(language, "target_help"))
    run.add_argument(
        "--output",
        type=Path,
        default=Path("rewindpy-report.html"),
        help=text(language, "output_help"),
    )
    run.add_argument(
        "--max-events",
        type=int,
        default=5_000,
        help=text(language, "max_events_help"),
    )
    run.add_argument(
        "--include",
        action="append",
        type=Path,
        default=[],
        help=text(language, "include_help"),
    )
    run.add_argument(
        "--exclude",
        action="append",
        type=Path,
        default=[],
        help=text(language, "exclude_help"),
    )
    run.add_argument(
        "--open",
        action="store_true",
        dest="open_report",
        help=text(language, "open_help"),
    )

    demo = subparsers.add_parser(
        "demo",
        help=text(language, "demo_help"),
        description=text(language, "demo_help"),
    )
    demo.add_argument(
        "kind",
        nargs="?",
        choices=demo_names(),
        default="none-origin",
        help=text(language, "demo_kind_help"),
    )
    demo.add_argument(
        "--output",
        type=Path,
        default=Path("rewindpy-demo.html"),
        help=text(language, "output_help"),
    )
    demo.add_argument(
        "--max-events",
        type=int,
        default=5_000,
        help=text(language, "max_events_help"),
    )
    demo.add_argument(
        "--open",
        action="store_true",
        dest="open_report",
        help=text(language, "open_help"),
    )

    doctor = subparsers.add_parser(
        "doctor",
        help=text(language, "doctor_help"),
        description=text(language, "doctor_help"),
    )
    doctor.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help=text(language, "json_help"),
    )
    return parser


def _split_target_args(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" not in argv:
        return argv, []
    separator = argv.index("--")
    return argv[:separator], argv[separator + 1 :]


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    try:
        language, localized_argv = _extract_language(raw_argv)
    except ValueError as exc:
        fallback = normalize_language(None)
        parser = build_parser(fallback)
        if exc.args and exc.args[0] is not None:
            parser.error(text(fallback, "invalid_language", value=exc.args[0]))
        parser.error(text(fallback, "missing_language"))

    rewind_args, target_args = _split_target_args(localized_argv)
    parser = build_parser(language)
    args = parser.parse_args(rewind_args)

    if args.command == "doctor":
        result = run_doctor()
        output = (
            format_doctor_json(result)
            if args.json_output
            else format_doctor_report(result, language)
        )
        print(output)
        return 0 if result.ready else 1

    if args.command == "demo":
        try:
            report = create_demo_report(
                args.kind,
                output=args.output,
                max_events=max(10, args.max_events),
                open_report=args.open_report,
                language=language,
            )
        except ValueError:
            parser.error(text(language, "unknown_demo", kind=args.kind))
        except RuntimeError:
            parser.error(text(language, "demo_failed"))
        print(text(language, "demo_report", path=report))
        return 0

    if args.command == "run":
        try:
            exit_code = run_target(
                args.target,
                target_args,
                output=args.output,
                max_events=max(10, args.max_events),
                language=language,
                include_paths=args.include,
                exclude_paths=args.exclude,
            )
        except FileNotFoundError:
            parser.error(text(language, "target_not_found", path=args.target))

        if exit_code != 0 and args.output.exists():
            report = args.output.resolve()
            print(
                "\n" + text(language, "captured_crash", path=report),
                file=sys.stderr,
            )
            if args.open_report:
                webbrowser.open(report.as_uri())
        return exit_code

    return 2
